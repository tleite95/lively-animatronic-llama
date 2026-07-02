# Secure, Isolated UTM Ubuntu VM (Apple Virtualization, arm64) — Setup Guide

*Note: As the title suggests, this guide is specifically aimed at setting up on a Mac with Apple Silicon and using UTM as the VM software. I have included instructions for Ubuntu and Windows where I feel confident in my ability to do so, but those instructions remain untested*

## Threat model and core principle

You want isolation that holds even if code running *inside* the VM is malicious and has root. That means:

- Anything enforced only **inside the guest** (ufw, guest-side resolv.conf, etc.) is not trustworthy on its own — malicious code with root can disable it.
- Real enforcement has to live **outside the VM's control**: on the macOS host's network stack (`pf`), and on a proxy process the guest cannot reach the configuration of.
- Guest-side controls are still worth doing as defense-in-depth, but treat the host-side firewall + whitelist proxy as the actual security boundary.

Architecture:

```
[Ubuntu VM] --(NAT, vmnet/bridge100)--> [macOS pf: default-deny] --> [Squid whitelist proxy on host] --> Internet
                                              |
                                   only exception: host -> VM:22 (SSH, host-initiated)
```
---

## 0. Terminology
- **VM** - Virtual machine. A sandboxed computer within your computer. Sometimes, the system running in the VM is called the "guest".
- **Host** - The computer running the VM. This is probably your laptop / desktop. If this guide tells you to do something on your host, it means to run it in your normal terminal, not in the VM
- **UTM** A specific piece of software for creating and running virtual machines. It is a very good, open-source option but it is Mac-exclusive. On Linux, you can use KVM with QEMU. On Windows, you can use VirtualBox. I have heard VMWare Fusion is good but I have never used it and don't know if it requires a license. This tutorial is specifically for UTM but you should be able to look up equivalent instructions for whatever VM software you end up using.
- **Firewall** -  Roughly speaking, a firewall is a piece of software that lets you write rules about what kinds of messages you can send and recieve over a network. This guide uses pf (packet filter) which is the standard for Mac and FreeBSD. Ubuntu hosts should use UFW (not covered in this guide) and Windows hosts can probably use Windows Firewall but have not looked into it.
- **Proxy** - A web server that takes requests sent to a given address and forwards them somewhere else. It also allows us to write some rules about what traffic gets let through. In our case, it is how we apply a whitelist to the VM's net requests and also how we route the requests between the internet and the VM
- **Daemon** - A background process, usually run that automatically starts when you turn on your computer.

---

## 1. VM creation settings (UTM)

When creating the VM:

- **Backend**: Apple Virtualization (not QEMU) — has a smaller/more constrained device surface than QEMU's emulated hardware, which is good for isolation.
- **Architecture**: arm64 (native on M2) — avoids TCG emulation entirely, which is both faster and reduces attack surface vs. emulating x86.
- **Network**: Set to **Shared Network** (NAT), *not* Bridged. Bridged puts the VM directly on your LAN as a peer; NAT routes everything through the host, which is what lets you filter it with `pf`. Most of the guide will be a lot of work to do nothing if you have a bridged network.
- **Sharing settings** (UTM → VM → Settings → Sharing):
  - **Shared Directory / Directory Share: set to None.** Do not add any shared folder, ever. This is the single most important setting — it's the difference between "no host filesystem access path exists" and "host filesystem access path exists but I hope nothing uses it."
  - **Clipboard Sharing: set to None.** Disable in both directions. Malicious code can be written to your paste buffer and act as a vector into your host system.
  - Disable USB device sharing, disable any drag-and-drop file transfer feature if present.
- Don't enable Rosetta/x86 translation if you don't need x86 binaries — fewer enabled subsystems is fewer things to harden.
- In your host machine  (Mac only!) , explicitly turn off **System Settings → General → Sharing → Remote Login**. This is additional hardening against the VM reaching the host's own sshd. Firewall rules in step 2 should block it, but it's nice to have fewer entry vectors just in case the firewall crashes, etc.

**Snapshot/clone immediately after hardened setup**, before ever running the agent workflow. UTM's Apple Virtualization backend has more limited snapshot support than its QEMU backend in some versions — check `VM → Snapshots` for availability. If snapshots aren't reliably supported for your UTM version, an equivalent approach: stop the VM, right click, select "Clone...".

This is instant and space-efficient on APFS. Not sure about Windows or Linux hosts, but I assume the same as long as you use a dynamic disk for `/home`

---

## 2. Host-side firewall (`pf`) — the real enforcement layer

**WARNING:** pf is a firewall software that runs on Mac and FreeBSD. If your host is Ubuntu, you will have to use ufw (I don't have instructions for that here). Not sure what you would use on Windows.

First, identify the host-side interface UTM's NAT uses. Start the VM, then on the host:

```bash
ifconfig | grep -A4 bridge100
```

(Exact interface name — `bridge100`, a `utun*`, or similar — can vary by macOS version; confirm it before writing rules. Also note the gateway IP, typically something like `192.168.64.1`, and the VM's subnet, e.g. `192.168.64.0/24`.)

<i>Quick note:</i> You can probably just assume the number after the slash will be 24, but to double check, look at the subnet mask you get from running ifconfig. It will be something like 255.255.255.0 convert this to binary: `11111111.11111111.11111111.00000000` then count the number of ones in the binary version. Or just look up a subnet calculator online.

Create `/etc/pf.anchors/com.vmfilter`:

```
vm_if = "bridge100"
vm_net = <vm subnet>
proxy = <gateway IP>
proxy_port = "3128"

# Allow VM -> host whitelist proxy only
pass in quick on $vm_if proto tcp from $vm_net to $proxy port $proxy_port keep state

# Allow host -> VM:22 (SSH); state table covers VM's response packets
pass out quick on $vm_if proto tcp from any to $vm_net port 22 keep state

# Final catch-all (redundant given default block above, kept for clarity)
block log in quick on $vm_if from $vm_net to any
```

Reference this anchor from `/etc/pf.conf` (back up the original first), then load and enable:

```bash
sudo cp /etc/pf.conf /etc/pf.conf.bak
echo 'anchor "com.vmfilter"' | sudo tee -a /etc/pf.conf
echo 'load anchor "com.vmfilter" from "/etc/pf.anchors/com.vmfilter"' | sudo tee -a /etc/pf.conf
sudo pfctl -e -f /etc/pf.conf
```

 To persist across reboots, wrap the command in a LaunchDaemon. There are ways to do this no matter what OS you are running, but the following are Mac-exclusive instrucitons, sorry.  To do this,

Create `/Library/LaunchDaemons/com.vmfilter.pf.plist`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vmfilter.pf</string>
    <key>RunAtLoad</key>
    <true/>
    <key>ProgramArguments</key>
    <array>
        <string>/sbin/pfctl</string>
        <string>-e</string>
        <string>-f</string>
        <string>/etc/pf.conf</string>
    </array>
</dict>
</plist>
```
Change ownership of the .plist file and add the daemon to launchctl
```
sudo chown root:wheel /Library/LaunchDaemons/com.vmfilter.pf.plist
sudo chmod 644 /Library/LaunchDaemons/com.vmfilter.pf.plist
sudo launchctl load /Library/LaunchDaemons/com.vmfilter.pf.plist
```

By default, pf logs are real-time only and you can't open up an file to see what events were logged in the past. In order to have a log that can be referenced, you can make another daemon that dumps logs to disk. Like with the previous daemon, these instrutions are for Mac only.

Create `/Library/LaunchDaemons/com.vmfilter.pflog.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vmfilter.pflog</string>
    <key>RunAtLoad</key>
    <true/>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/sbin/tcpdump</string>
        <string>-w</string>
        <string>/var/log/pflog</string>
        <string>-i</string>
        <string>pflog0</string>
    </array>
</dict>
</plist>
```

Change ownership for this one too
```bash
sudo chown root:wheel /Library/LaunchDaemons/com.vmfilter.pflog.plist
sudo chmod 644 /Library/LaunchDaemons/com.vmfilter.pflog.plist
sudo launchctl load /Library/LaunchDaemons/com.vmfilter.pflog.plist
```

Then to view the log:

```bash
sudo tcpdump -n -e -ttt -r /var/log/pflog
```

Notes:
- You don't technically need to bother with all the LaunchDaemon stuff. You can also restart pfctl every time you reboot your host: `pfctl -e -f /etc/pf.conf`
- On recent macOS, `pf` coexists with the Application Firewall and other system uses of pf; test carefully, ideally with the VM stopped first, then start the VM and confirm `pfctl -sr` shows your rules still loaded.
- If you find raw `pf` unreliable to manage long-term, a GUI alternative for the same effect is a host-level outbound firewall like **Little Snitch** or **LuLu**, scoped to deny the UTM process / vmnet subnet by default and allow only the proxy port.

---

## 3. Whitelist proxy (Squid) on the host


**WARNING:** squid is a proxy that runs on Mac and Linux. You can run it on Windows via WSL, but I am not sure about how to do it if you want to use PowerShell.

Install on the Host (not the VM):

Mac:
```bash
brew install squid
```

Ubuntu:
```bash
sudo apt-get install squid
```

Config
- `/opt/homebrew/etc/squid.conf` on Apple Silicon
- `/etc/squid/squid.conf` on Ubuntu
```
http_port 192.168.64.1:3128

acl vm_net src 192.168.64.0/24
acl whitelist dstdomain "/opt/homebrew/etc/squid/whitelist.txt"

http_access allow vm_net whitelist
http_access deny all
```
**Note**: if you are doing this on Ubuntu, make sure you use the Ubuntu version of path below to the whitelist file in the line that starts "acl whitelist..."


Create the whitelist (one domain per line, leading dot matches subdomains all subdomains, no leading dot matches only the domain)
- `/opt/homebrew/etc/squid/whitelist.txt` (Apple Silicon)
- `/etc/squid/whitelist.txt` (Ubuntu)

```
.github.com
.githubusercontent.com
.api.github.com
.api.githubcopilot.com
.pypi.org
.npmjs.org
.ubuntu.com
.launchpad.net
.opencode.ai
```

For this specific project, you may also want to add some more domains to the whitelist. Particularly, the llmoxie API url and potentially some research paper servers since they will be helpful for fetching research papers, etc.
```
<llmoxie API url>
.ncbi.nlm.nih.gov
serpapi.com
scholar.google.com
pubs.acs.org
pdf.sciencedirectassets.com
sciencedirect.com
```

Start it:

On Mac: 
```bash
brew services start squid
```
On ubuntu:
```bash
sudo systemctl enable squid
sudo systemctl start squid
```


Because this is a standard forwarding proxy (HTTP `CONNECT` tunneling for HTTPS), Squid can allow/deny based on the SNI hostname in the `CONNECT` request **without decrypting TLS** — no need for `ssl_bump` or installing a fake CA certificate in the guest. That keeps end-to-end TLS intact and the setup simpler.

In the guest (Ubuntu), point everything at the proxy. Edit `/etc/environment`:

```
http_proxy="http://192.168.64.1:3128/"
https_proxy="http://192.168.64.1:3128/"
no_proxy="localhost,127.0.0.1"
```

Also configure per-tool proxies as needed. Unfortunately, apt, git, npm, and some others do not respect the environment proxy. If a program is timing out when it tries to connect to the internet, your first thing to check should be if it has a specific way to configure its http proxy.

For apt, edit `/etc/apt/apt.conf.d/95proxies`

```
Acquire::http::Proxy "http://192.168.64.1:3128/";
Acquire::https::Proxy "http://192.168.64.1:3128/";
```

Each tool is going to have its own way to tell it what proxy to use. It's really annoying, sorry.

**Important**: the guest proxy config is a convenience, not the security boundary. Even if a tool ignores the proxy entirely and tries to connect directly, the `pf` default-deny rule from Section 2 blocks it at the IP layer regardless. The whitelist is enforced by Squid; the *inability to bypass the whitelist* is enforced by `pf`.

**Note:** If you are having trouble accessing the proxy from the VM, you may have a permissions issue in your squid service. There is a quick fix, but please **only run this if you are the only user on your host computer**, since you might break other people's services otherwise. On your host:

```bash
sudo chown -R $(whoami):admin /opt/homebrew/var/run/ /opt/homebrew/var/logs/
```

---

## 4. SSH (host → VM)

In the guest, `/etc/ssh/sshd_config`:

```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers <vm user>
Subsystem sftp /usr/lib/openssh/sftp-server
```

Generate a key pair **on the host**, and only ever put the *public* key in the guest's `~/.ssh/authorized_keys`. Never put a private key inside the VM — there's no reason for the VM to need to SSH anywhere, let alone back to the host.

The easiest way to get your public key into the VM is to copy / paste. Since there is no agentic anything installed yet, it is safe to temporarily enable the clipboard, paste the contents of your pubkey into `~/.ssh/authorized_keys`, and then **remember to disable the clipboard again**.


SSH is one-way by construction: the VM never listens for or initiates anything toward the host's SSH; it's purely a host-initiated TCP session into the guest's sshd, and the `pf` rules in Section 2 only permit *response* traffic for that host-initiated session, not new VM-initiated connections.

**Optional step:**

You SSH into the VM using its gateway IP (found in step 2), which unfortunately can change dynamically between reboots. In order to prevent this, create a static netplan config. If you don't want to do this, you can get the IP automatically when you try to SSH into the VM. Instructions for that command at the bottom of this section.

First find your VM's MAC address by running this inside the VM:

```bash
ip link show
```

Look for the entry link/ether that looks like `xx:xx:xx:xx:xx:xx`, and where the letters and numbers aren't either all `0` or all `f`. Also note the link name of that entry (e.g. `enp0s1`)


In the vm, modify (or create): `/etc/netplan/00-installer-config.yaml`
```yaml
network:
  version: 2
  ethernets:
    <link name>:
      match:
        macaddress: <VM MAC address>
      dhcp4: no
      dhcp6: true
      addresses: [192.168.64.2/24]
      routes:
        - to: default
          via: 192.168.64.1
      nameservers:
        addresses: [192.168.64.1]
    set-name: <link name>
```

Then apply it (still in VM)
```bash
sudo systemctl restart networking
```

### How to make ssh and scp less painful
*You may not understand any of what's going on behind the scenes here to make this work and that's ok. I promise none of this will break your computer or like download a virus or anything*

If you don't want to set up a static IP for the VM, you can get it dynamically from your host's list of devices on its network. In UTM with a bridged network, the device should be under the entry: `bridge100`. So you can use the following:

`.aliasrc`
```bash
# Use a variable for the VM username so if it ever changes, you can update it in a single place.
VMUSER="<vm username>"

alias sshvm='ssh "$VMUSER"@$(arp -a | grep bridge100 | grep -oE "192\.168\.64\.[0-9]+" | grep -v "255")'
```

This becomes a bit of a hassle when trying to use scp, so you may want to define some helper bash functions in your .bashrc or .aliasrc file:

`.aliasrc`
```bash
# NOTE: These commands will send the files you scp over to /tmp/<whatever you call the file>

# scp from host -> VM
scpvm(){
	scp "$1" "$VMUSER"@$(arp -a | grep bridge100 | grep -oE "192\.168\.64\.[0-9]+" | grep -v "255"):/tmp/"$2"
}

# scp from VM -> host
vmscp(){
	scp "$VMUSER"@$(arp -a | grep bridge100 | grep -oE "192\.168\.64\.[0-9]+" | grep -v "255"):"$1" /tmp/"$2"
}
```
To use these, start a new terminal or within the same session, run
```bash
source ~/.aliasrc
```

---

## 5. DNS

Two options, pick based on how much the agent's tooling relies on direct DNS resolution:

**Option A — do nothing extra.** Since `pf` blocks all VM-originated traffic except to the proxy port, direct DNS queries (UDP/TCP 53) from the guest will simply time out. Anything using the proxy correctly doesn't need its own DNS resolution (Squid resolves on the proxy's behalf). The downside is tools that hard-require a successful DNS lookup before even trying the proxy may error out, even though the eventual connection would've been blocked anyway.

**Option B — filtering resolver on the host.** Run a local resolver (e.g. `dnsmasq`) bound to the vmnet interface, configured to default-deny resolution and only answer for your whitelisted domains; then add a narrow `pf` exception for VM → host:53 to that resolver only. This satisfies tools that need DNS to "work" without granting any actual additional network reach, since the underlying TCP/UDP destination is still blocked unless it's the proxy port.

Start with Option A; only add Option B if something in your workflow specifically breaks without working DNS.

---

## 6. Agentic GitHub Key

To make sure the agent doesn't wreak havok on other repositories your account has access to, (or even repositories it *does* have access to), it will use a special access token to perform its GitHub interactions. This allows us to have fine-grained control over what it is allowed to do and where.

1. Go to your GitHub account settings (top-left profile icon > Settings)
2. On the left, scroll down and go to `Developer Settings`
3. On the left, go to `Personal Access Tokens > Fine-grained tokens`
4. Generate a new token
    * Give your token a name. It doesn't really matter what this is, just something that notes that this is for an AI agent and specific to a given repo
    * Optionally add a descrption
    * Set it to expire some time shortly after the end of the program
    * Under `Repository Access`, select `Only select repositories` and then choose your fork of the project.
    * Add a permission for `Contents` and then set it to "Read and write". Alternatively, you can give it read-only access but then it might be a bit of a pain to actually push your changes.
5. Done! Hit "Generate token"
    * **WARNING**  Once you click create, you must copy the PAT you generate and save it somewhere secure.


The PAT means the agent won't be able to mess with any repositories other than the ones you specifically allow it to. However, they can still erase all of your work in that repository if something goes wrong. In order to safeguard against this, add some protections to your repo. Navigate to the settings of your fork of the project on GitHub (the URL will look like `https://github.com/<your username>/<repo>/settings`). On the left menu, go to `Rules > Rulesets` and then click `New ruleset > New branch ruleset`.
1. Give the ruleset a name. It can be anything
2. Set the enforcement status to "enabled"
3. Leave the bypass list empty
4. Add a target, you can select either "Include default branch" if you only want to protect main, or "Include all branches" if you want to protect the whole repo. I recommend just including the default branch but either is fine.
5. Add the following branch rules (some may be selected by default):
* Restrict deletions
* Require a pull request before merging
    * Required reviewers: 0
* Block force pushes
6. Done! Hit "Create"


**NOTE:** This rest of this step requires you to have already set up opencode. That is not in the scope of this document. I recommend finishing your VM setup and testing everything except the PAT. Then, clone the VM image so you have a clean backup with no agents even installed. Once you have a clean backup, come back to this step and you can proceed to install your PAT into opencode.

Since we are using opencode, there is an easy way to add your PAT to its config so it can automatically use it. Just modify your opencode config by adding an "mcp" field. Make sure you include the text `Bearer ` including the trailing space before you paste your PAT or else it won't work.

`opencode.jsonc`:
```json
{
    ... rest of your config file...

    "mcp": {
        "github": {
            "type": "remote",
            "url": "https://api.githubcopilot.com/mcp/",
            "headers": {
                "Authorization": "Bearer <PAT>"
            }
        }
    }
}
```

You will also need git installed on your VM:
```bash
sudo apt-get install git
```

If the repo is public, you should be able to clone it no problem. If it is private, you can probably use the PAT to clone it somehow, but I recommend just using scp to send over the repo from your host and going from there. If you go that route and you have your remote set up to use ssh, you will have to change the remote to http:
```bash
git remote set-url origin https://github.com/<username>/<repo>.git
```

Once you have an https origin set up in your repo, you also need to configure git to use the proxy and to not prompt the user for inputs (opencode cannot deal with this)

```bash
git config http.proxy http://192.168.64.1:3128
git config https.proxy http://192.168.64.1:3128

git config --global credential.helper store
echo "https://<github username>:<PAT>@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

---

## 7. Verification checklist

Run these from inside the VM after setup:

```bash
# Should fail (timeout) — direct connection bypassing proxy
curl --connect-timeout 5 https://example.com

# Should succeed — whitelisted domain via proxy
curl -x http://192.168.64.1:3128 https://github.com

# Should fail with 403 from Squid — non-whitelisted domain via proxy
curl -x http://192.168.64.1:3128 https://some-random-site.com

# Should fail — VM trying to reach an arbitrary host port (simulate "no host access")
nc -zv 192.168.64.1 5900   # or any other host service port
```

**IMPORTANT:** If the VM-side `curl` to `example.com` direct succeeds, your `pf` rules aren't loaded/scoped correctly — stop and fix before running anything sensitive in the VM.

And from the host:

```bash
# Confirms SSH into host is disabled
ssh localhost

# Confirms pf rules are actually loaded
sudo pfctl -sr

# Confirms you can SSH into the VM
sshvm

# Try to scp something over
echo "test" > /tmp/test
scpvm /tmp/test test

```

Then back in the VM just ot make sure the scp worked

```bash
cat /tmp/test
```

## Other tests you should do (not covered)
The scope of this guide is only to cover how to set up the VM so that your agent can be totally isolated. It does not cover actually installing the agent and configuring it, except where that intersects with isolation (specifically, the PAT for GitHub). In order to test that, you will need to set up and configure opencode according to some other instructions. Once you do that, just get opencode to try and push something to GitHub. If it succeeds, your PAT is all set up correctly. You can also try to get it to break the access rules, e.g. force pushing to main. Make sure that request fails.

You can also get the agent to try and access online resources outside the whitelist or modify files on the host machine. Make sure it has no ability to do so, but **be careful with what you ask** because if there is a missed step in your setup, these can be extremely dangerous commands to run.

---

## 8. Additional isolation recommendations
*Full disclosure, the (human) author of this guide does the first three but not the last two.*
- **Keep UTM and macOS updated** — isolation guarantees depend on the Apple Virtualization framework's own boundary, which gets security patches over time.
- **Revert to a clean snapshot/clone before and after every agent run** (Section 1) — assume any given run could leave persistence mechanisms, and don't trust the guest's own state.
- **Review Logs** — Review pf's `/var/log/pflog` and Squid's `access.log` periodically; this gives you visibility into what the agent is *trying* to reach, which is useful both for catching misconfigurations and for noticing anomalous behavior.
- **Run UTM under a separate, dedicated macOS user account** — not the account that holds your sensitive files. Combined with no shared folders, this means there's no filesystem path *and* no OS-level permission grant for the VM's host process to reach your normal files, as a second independent layer.
- **Run the agent inside the VM as a non-root user** with `sudo` either disabled or password-gated. This doesn't affect host isolation, but limits what a compromised agent process can do even within the guest (e.g., can't tamper with sshd config or pf-adjacent guest settings, can't read other local users' files if you add any).


---

# Disclaimer
First draft generated by claude.ai, Sonnet 4.6, medium effort. I edited some parts that were unclear or incorrect and added a few sections as well. Anything related to how to do this on Ubuntu or Windows is from me, since the prompt explicitly mentioned my Mac setup. Additionally, I wrote the section on GitHub keys by hand. All told, this document is probably close to 50% AI generated and 50% human generated. All the AI generated parts have been checked by a human for accuracy and safety.

All that being said, humans make mistakes too. If you notice anything wrong with this document, or if anything doesn't work, please notify the authors. As I said at the top of the document, this guide is specifically aimed at setting up on a Mac with Apple Silicon and using UTM as the VM software. I have included instructions for Ubuntu and Windows where I feel confident in my ability to do so, but those instructions remain untested.
## Prompt
### 
```
I want to securely set up UTM version 4.7.5 (118) with ubuntu on a host M2 Macbook Air (16GB unified memory). I am using Apple virtualization and my ubuntu architecture is arm64. The VM is being used to run an agentic workflow on a machine with other users, files, and programs that should not be accessible from within the VM in any way. I want:
* To have a whitelist for what web resources are available
* One-way ssh access from host -> VM

I do not want the VM to be able to modify any files on the host. I do not want the VM to be able to run any commands on the host, even if there is malicious code is present on the VM. If you have any other recommendations for complete isolation, point them out and include instructions for how to implement those recommendations.
```