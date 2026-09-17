#!/usr/bin/env python3
"""T4 bench: the client-class matrix against the deployed facade.

Runs on the operator's workstation, so its vantage is off-LAN (the router
sees it as 172.23.240.220 through the lab route): that is the *stricter*
vantage for containment, since a caller whose own address is not in the LAN
cannot satisfy a mapping request at all. The LAN vantage (a same-LAN control
point that can drive the mapping engine) is bench-lan-client.sh, run on the
router.

Sequences, per plan/0008 section 24's matrix:
  discovery : the v1, IGD:2, WIP:2, ssdp:all (deferred) and flip rows,
              with the deadline property measured
  xbox      : an IGD1-only control point
  syncthing : a v2 control point that does not speak DeviceProtection
  tailscale : a v2 control point that does, including the lift

Usage: python3 bench-matrix.py [--json out.json]
"""
import argparse, base64, hashlib, hmac, json, re, socket, subprocess, sys, time
import urllib.error, urllib.request

ROUTER = "root@192.168.21.1"
BASE = "http://192.168.21.1:49152"
URN1 = "urn:schemas-upnp-org:service:WANIPConnection:1"
URN2 = "urn:schemas-upnp-org:service:WANIPConnection:2"
URNDP = "urn:schemas-upnp-org:service:DeviceProtection:1"
SSDP = ("239.255.255.250", 1900)
SSDP_UNICAST = ("192.168.21.1", 1900)  # off-LAN: multicast does not route to br-lan
LAN_ENTRY = (34999, "UDP", "192.168.21.1")   # what bench-lan-client.sh creates
OWN_ENTRY = (34998, "UDP")                   # created and deleted by this vantage
# This workstation's address as the deployed device sees it. The router
# source-maps the lab path, so the address on this side (172.23.240.220) is
# not the one the facade keys sessions and containment on. Learned from the
# router's own ssh peer for the same host:
#   ssh root@192.168.21.1 'ss -tn state established "( sport = :22 )"'
CALLER = "192.168.21.97"
DEVICE_ID = bytes.fromhex("7f1285bae0d75f50a3d1be77702564c0")
CP_ID = bytes.fromhex("00112233445566778899aabbccddeeff")
USER, PASSWORD = "operator", b"bench-lan-2026"

TICK_MS = 250       # the receive tick while collecting answers
FLIP_DELAY_MS = 50  # how long after an ssdp:all the flip probe is sent

RESULTS = []


def check(name, expected, observed, ok):
    RESULTS.append({"probe": name, "expected": expected,
                    "observed": observed, "pass": bool(ok)})
    print(f"[{'PASS' if ok else 'FAIL'}] {name:52} {observed}")
    return ok


def soap(url, urn, action, args):
    body = (f'<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            f's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
            f'<u:{action} xmlns:u="{urn}">{args}</u:{action}></s:Body></s:Envelope>')
    req = urllib.request.Request(url, data=body.encode(),
                                 headers={"SOAPACTION": f'"{urn}#{action}"',
                                          "Content-Type": 'text/xml; charset="utf-8"'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def err(xml):
    m = re.search(r"<errorCode>(\d+)</errorCode>", xml)
    return m.group(1) if m else ""


def tag(xml, name):
    m = re.search(rf"<{name}>(.*?)</{name}>", xml, re.S)
    return m.group(1) if m else ""


def msearch(st, mx=1, wait=3.0, extra=None):
    """Send one M-SEARCH and collect the answers, with arrival times."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.settimeout(TICK_MS / 1000)
    msg = (f"M-SEARCH * HTTP/1.1\r\nHOST: {SSDP[0]}:{SSDP[1]}\r\nMAN: \"ssdp:discover\"\r\n"
           f"MX: {mx}\r\nST: {st}\r\n\r\n").encode()
    t0 = time.time()
    s.sendto(msg, SSDP_UNICAST)
    if extra:
        time.sleep(extra[1] / 1000)
        s.sendto(extra[0].encode(), SSDP_UNICAST)
    out = []
    while time.time() - t0 < wait:
        try:
            data, _ = s.recvfrom(4096)
        except socket.timeout:
            continue
        out.append((time.time() - t0, data.decode(errors="replace")))
    s.close()
    return out


def line(resp, key):
    m = re.search(rf"^{key}: (.*)$", resp, re.M | re.I)
    return m.group(1).strip() if m else ""


def st_of(resp):
    return line(resp, "ST")


def loc(resp):
    return line(resp, "LOCATION")


# ---------------------------------------------------------------- discovery
def discovery():
    print("\n== discovery rows (the test matrix) ==")
    rows = [("upnp:rootdevice", "upnp:rootdevice", "/igd/v1/"),
            ("urn:schemas-upnp-org:device:InternetGatewayDevice:1",
             "urn:schemas-upnp-org:device:InternetGatewayDevice:1", "/igd/v1/"),
            ("urn:schemas-upnp-org:device:InternetGatewayDevice:2",
             "urn:schemas-upnp-org:device:InternetGatewayDevice:2", "/igd/v2/"),
            ("urn:schemas-upnp-org:service:WANIPConnection:2",
             "urn:schemas-upnp-org:service:WANIPConnection:2", "/igd/v2/")]
    for st, want_st, want_loc in rows:
        got = msearch(st, wait=2.0)
        ok = bool(got) and st_of(got[0][1]) == want_st and want_loc in loc(got[0][1])
        check(f"M-SEARCH {st}", f"{want_st} + {want_loc}",
              f"{st_of(got[0][1]) if got else 'no answer'} {loc(got[0][1]) if got else ''}", ok)

    # ssdp:all with nothing else in the burst: deferred, then v1
    got = msearch("ssdp:all", mx=1, wait=3.0)
    delay = got[0][0] if got else -1
    ok = (bool(got) and "/igd/v1/" in loc(got[0][1])
          and 850 <= delay * 1000 <= 1800)
    check("ssdp:all alone: deferred v1 at the debounce deadline",
          "v1 answer, 850-1800 ms", f"{loc(got[0][1]) if got else 'none'} at {delay * 1000:.0f} ms", ok)

    # ssdp:all then an explicit :2 inside the window: both answers are v2
    got = msearch("ssdp:all", mx=1, wait=3.5,
                  extra=(f"M-SEARCH * HTTP/1.1\r\nHOST: {SSDP[0]}:{SSDP[1]}\r\n"
                         f"MAN: \"ssdp:discover\"\r\nMX: 1\r\n"
                         f"ST: urn:schemas-upnp-org:device:InternetGatewayDevice:2\r\n\r\n", FLIP_DELAY_MS))
    v2 = [g for g in got if "/igd/v2/" in loc(g[1])]
    check("ssdp:all + :2 in the window flips the burst", "both answers v2",
          f"{len(got)} answer(s), {len(v2)} on v2", bool(got) and len(v2) == len(got))


# ------------------------------------------------------------------- xbox
def xbox():
    print("\n== xbox-class: an IGD1-only control point ==")
    code, body = soap(f"{BASE}/ctl/IPConn", URN1, "GetExternalIPAddress", "")
    ip = tag(body, "NewExternalIPAddress")
    check("v1 GetExternalIPAddress", "200 + a public address", f"{code} {ip}", code == 200 and ip)

    code, body = soap(f"{BASE}/ctl/IPConn", URN1, "AddPortMapping",
                      '<NewRemoteHost></NewRemoteHost><NewExternalPort>34998</NewExternalPort>'
                      '<NewProtocol>UDP</NewProtocol><NewInternalPort>34998</NewInternalPort>'
                      '<NewInternalClient>192.168.21.50</NewInternalClient><NewEnabled>1</NewEnabled>'
                      '<NewPortMappingDescription>bench-other</NewPortMappingDescription>'
                      '<NewLeaseDuration>3600</NewLeaseDuration>')
    check("v1 AddPortMapping naming another host", "606 (containment)",
          f"{code} err={err(body)}", err(body) == "606")

    code, body = soap(f"{BASE}/ctl/IPConn", URN1, "GetGenericPortMappingEntry",
                      "<NewPortMappingIndex>0</NewPortMappingIndex>")
    check("v1 enumeration with nothing visible", "714 (contained index space)",
          f"{code} err={err(body)}", err(body) == "714")

    code, body = soap(f"{BASE}/ctl/IPConn", URN1, "GetSpecificPortMappingEntry",
                      '<NewRemoteHost></NewRemoteHost><NewExternalPort>%d</NewExternalPort>'
                      '<NewProtocol>%s</NewProtocol>' % (LAN_ENTRY[0], LAN_ENTRY[1]))
    check("v1 read of the LAN client's entry", "606 (containment)",
          f"{code} err={err(body)}", err(body) == "606")



def own_mapping():
    """The caller may map for itself (its own address, a high port), which is
    the clause the containment exists to bound. This creates a real mapping,
    so it is deleted at the end of the run."""
    ext = OWN_ENTRY[0]
    code, body = soap(f"{BASE}/ctl/IPConn", URN1, "AddPortMapping",
                      f'<NewRemoteHost></NewRemoteHost><NewExternalPort>{ext}</NewExternalPort>'
                      f'<NewProtocol>{OWN_ENTRY[1]}</NewProtocol><NewInternalPort>{ext}</NewInternalPort>'
                      f'<NewInternalClient>{CALLER}</NewInternalClient><NewEnabled>1</NewEnabled>'
                      '<NewPortMappingDescription>bench-self</NewPortMappingDescription>'
                      '<NewLeaseDuration>3600</NewLeaseDuration>')
    check("v1 AddPortMapping naming the caller's own address", "200 (its own host, high port)",
          f"{code} err={err(body)}", code == 200 and not err(body))

    # and it is visible to that caller, because it is its own
    code, body = soap(f"{BASE}/ctl/IPConn", URN1, "GetSpecificPortMappingEntry",
                      f'<NewRemoteHost></NewRemoteHost><NewExternalPort>{ext}</NewExternalPort>'
                      f'<NewProtocol>{OWN_ENTRY[1]}</NewProtocol>')
    check("v1 read of the caller's own entry", "200 + the label it set",
          f"{code} {tag(body, 'NewPortMappingDescription')}",
          code == 200 and tag(body, "NewPortMappingDescription") == "bench-self")


def cleanup_own():
    ext = OWN_ENTRY[0]
    code, body = soap(f"{BASE}/ctl/IPConn", URN1, "DeletePortMapping",
                      f'<NewRemoteHost></NewRemoteHost><NewExternalPort>{ext}</NewExternalPort>'
                      f'<NewProtocol>{OWN_ENTRY[1]}</NewProtocol>')
    check("v1 DeletePortMapping of the caller's own entry", "200",
          f"{code} err={err(body)}", code == 200 and not err(body))


# -------------------------------------------------------------- syncthing
def syncthing():
    print("\n== syncthing-class: a v2 control point without DeviceProtection ==")
    code, body = soap(f"{BASE}/ctl/IPConn", URN2, "GetExternalIPAddress", "")
    check("v2 GetExternalIPAddress", "200", f"{code} {tag(body, 'NewExternalIPAddress')}", code == 200)

    for action, args, want in [
        ("AddPortMapping", '<NewRemoteHost></NewRemoteHost><NewExternalPort>34997</NewExternalPort>'
                           '<NewProtocol>UDP</NewProtocol><NewInternalPort>34997</NewInternalPort>'
                           '<NewInternalClient>192.168.21.1</NewInternalClient><NewEnabled>1</NewEnabled>'
                           '<NewPortMappingDescription>bench</NewPortMappingDescription>'
                           '<NewLeaseDuration>3600</NewLeaseDuration>', "606"),
        ("AddAnyPortMapping", '<NewRemoteHost></NewRemoteHost><NewExternalPort>0</NewExternalPort>'
                              '<NewProtocol>UDP</NewProtocol><NewInternalPort>34997</NewInternalPort>'
                              '<NewInternalClient>192.168.21.1</NewInternalClient><NewEnabled>1</NewEnabled>'
                              '<NewPortMappingDescription>bench</NewPortMappingDescription>'
                              '<NewLeaseDuration>0</NewLeaseDuration>', "606"),
        ("DeletePortMappingRange", '<NewStartPort>34990</NewStartPort><NewEndPort>35000</NewEndPort>'
                                   '<NewProtocol>UDP</NewProtocol><NewManage>1</NewManage>', "606"),
    ]:
        code, body = soap(f"{BASE}/ctl/IPConn", URN2, action, args)
        check(f"v2 {action} unauthenticated", f"{want} (the boundary)",
              f"{code} err={err(body)}", err(body) == want)

    code, body = soap(f"{BASE}/ctl/IPConn", URN2, "GetListOfPortMappings",
                      '<NewStartPort>1</NewStartPort><NewEndPort>65535</NewEndPort>'
                      '<NewProtocol>UDP</NewProtocol><NewManage>0</NewManage>'
                      '<NewNumberOfPorts>0</NewNumberOfPorts>')
    check("v2 listing, unauthenticated, other hosts' entries present", "730 (contracted view)",
          f"{code} err={err(body)}", err(body) == "730")

    for action, args, want in [
        ("GetNATRSIPStatus", "", "NewNATEEnabled>1"),
        ("SetConnectionType", "<NewConnectionType>IP_Routed</NewConnectionType>", "731"),
        ("ForceTermination", "", "501"),
        ("RequestConnection", "", "200"),
        ("GetListOfPortMappings", '<NewStartPort>1</NewStartPort><NewEndPort>65535</NewEndPort>'
                                  '<NewProtocol>UDP</NewProtocol><NewManage>0</NewManage>'
                                  '<NewNumberOfPorts>0</NewNumberOfPorts>', "730"),
    ]:
        code, body = soap(f"{BASE}/ctl/IPConn", URN2, action, args)
        if action == "GetNATRSIPStatus":
            ok = "NewNATEEnabled>1" in body and "NewRSIPAvailable>0" in body
            check("v2 GetNATRSIPStatus", "RSIP 0 / NAT 1", f"{code} {body[body.find('NewRSIP'):][:64]}", ok)
        elif action == "RequestConnection":
            check("v2 RequestConnection", "200 (the line is up)", f"{code} err={err(body)}", code == 200)
        else:
            check(f"v2 {action}", f"{want}", f"{code} err={err(body)}",
                  err(body) == want if want != "200" else code == 200)


# --------------------------------------------------------------- tailscale
def tailscale():
    print("\n== tailscale-class: a v2 control point that speaks DeviceProtection ==")
    code, body = soap(f"{BASE}/ctl/DP", URNDP, "GetSupportedProtocols", "")
    names = re.findall(r"<Name>(.*?)</Name>", body)
    check("DP GetSupportedProtocols", "WPS and PKCS5 present",
          f"{code} {names}", code == 200 and "WPS" in names and "PKCS5" in names)

    code, body = soap(f"{BASE}/ctl/DP", URNDP, "GetAssignedRoles", "")
    pre = tag(body, "RoleList")
    check("DP GetAssignedRoles before login", "Public", f"{code} {pre!r}", pre == "Public")

    code, body = soap(f"{BASE}/ctl/DP", URNDP, "GetUserLoginChallenge",
                      f"<ProtocolType>PKCS5</ProtocolType><Name>{USER}</Name>")
    if code != 200:
        check("DP GetUserLoginChallenge", "200 + Salt and Challenge",
              f"{code} err={err(body)}", False)
        return
    salt, chal_b64 = tag(body, "Salt"), tag(body, "Challenge")
    stored = hashlib.pbkdf2_hmac("sha256", PASSWORD, USER.encode() + base64.b64decode(salt), 5000)[:16]
    mac = hmac.new(stored, base64.b64decode(chal_b64) + DEVICE_ID + CP_ID, hashlib.sha256).digest()[:16]
    check("DP GetUserLoginChallenge", "Salt + Challenge issued",
          f"Salt={salt[:12]}... Challenge={chal_b64[:12]}...", bool(salt and chal_b64))

    code, body = soap(f"{BASE}/ctl/DP", URNDP, "UserLogin",
                      f"<ProtocolType>PKCS5</ProtocolType><Challenge>{chal_b64}</Challenge>"
                      f"<Authenticator>{base64.b64encode(mac).decode()}</Authenticator>")
    check("DP UserLogin with the PKCS5 authenticator", "200",
          f"{code} err={err(body)}", code == 200)

    code, body = soap(f"{BASE}/ctl/DP", URNDP, "GetAssignedRoles", "")
    post = tag(body, "RoleList")
    check("DP GetAssignedRoles after login", "Basic (the lift)", f"{code} {post!r}", post == "Basic")

    # the lift: the same reads that were contracted become whole
    ext, proto, client = LAN_ENTRY
    code, body = soap(f"{BASE}/ctl/IPConn", URN2, "GetSpecificPortMappingEntry",
                      f'<NewRemoteHost></NewRemoteHost><NewExternalPort>{ext}</NewExternalPort>'
                      f'<NewProtocol>{proto}</NewProtocol>')
    check("v2 read of the LAN client's entry, lifted", "200 + the entry",
          f"{code} {tag(body, 'NewInternalClient')} {tag(body, 'NewPortMappingDescription')}",
          code == 200 and tag(body, "NewInternalClient") == client)

    # the lifted view holds every entry, so walk it for the LAN client's
    walked = []
    for i in range(8):
        code, body = soap(f"{BASE}/ctl/IPConn", URN2, "GetGenericPortMappingEntry",
                          f"<NewPortMappingIndex>{i}</NewPortMappingIndex>")
        if code != 200:
            break
        walked.append(tag(body, "NewExternalPort"))
    check("v2 enumeration, lifted", f"the walk reaches ext {ext}",
          f"indexes={walked}", str(ext) in walked)

    code, body = soap(f"{BASE}/ctl/IPConn", URN2, "GetListOfPortMappings",
                      '<NewStartPort>1</NewStartPort><NewEndPort>65535</NewEndPort>'
                      '<NewProtocol>UDP</NewProtocol><NewManage>0</NewManage>'
                      '<NewNumberOfPorts>0</NewNumberOfPorts>')
    check("v2 listing, lifted", "200 + a PortMappingEntry",
          f"{code} entries={body.count('<p:PortMappingEntry>')}",
          code == 200 and "<p:PortMappingEntry>" in body and "bench-lan" in body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    args = ap.parse_args()

    # A DeviceProtection session outlives one bench run, and a lift is a
    # principal's roles rather than a face's, so an un-logged-out session from
    # an earlier run would lift every containment below. Log out first and
    # prove the roles are Public, which is what makes the refusals meaningful.
    print("== session state ==")
    code, body = soap(f"{BASE}/ctl/DP", URNDP, "UserLogout", "")
    print(f"UserLogout: {code} err={err(body)}")
    code, body = soap(f"{BASE}/ctl/DP", URNDP, "GetAssignedRoles", "")
    print(f"GetAssignedRoles after logout: {tag(body, 'RoleList')!r}")

    # the LAN vantage creates the entry the contained reads must hide
    print("== LAN vantage: create the entry the contained reads must hide ==")
    out = subprocess.run(["ssh", "-o", "BatchMode=yes", ROUTER,
                          "sh -s create"], input=open("bench-lan-client.sh").read(),
                         capture_output=True, text=True, timeout=60)
    print(out.stdout + out.stderr)

    code, body = soap(f"{BASE}/ctl/IPConn", URN2, "GetGenericPortMappingEntry",
                      "<NewPortMappingIndex>0</NewPortMappingIndex>")
    print(f"the LAN entry, as its owner sees it: {code} ext={tag(body, 'NewExternalPort')} "
          f"desc={tag(body, 'NewPortMappingDescription')}")

    discovery()
    xbox()
    syncthing()
    tailscale()
    own_mapping()

    print("\n== LAN vantage: clean up ==")
    out = subprocess.run(["ssh", "-o", "BatchMode=yes", ROUTER,
                          "sh -s clean"], input=open("bench-lan-client.sh").read(),
                         capture_output=True, text=True, timeout=60)
    print(out.stdout + out.stderr)

    cleanup_own()

    npass = sum(1 for r in RESULTS if r["pass"])
    print(f"\n== bench matrix: {npass}/{len(RESULTS)} passed ==")
    for r in RESULTS:
        if not r["pass"]:
            print(f"   FAIL {r['probe']}: expected {r['expected']}, saw {r['observed']}")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(RESULTS, f, indent=2)
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())