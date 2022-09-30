# git-caching-proxy
Speed up repeated git clones / fetches and reduce network traffic

## What is this?

The name is very straightforward: this is a caching proxy server for Git.

Once set up, the proxy server will maintain an up-to-date copy of any remote repositories you clone / fetch through it.
This means cloning the same repository repeatedly will use much less network traffic, and as a result be much faster.
A lot of time will be saved if, for example, you have a `RUN git clone ...` command in your Dockerfile.

### Advantages

* Uses the original `git` commands: just `git clone` as usual, no need to remember a different command
* Can `git config` to use for all or some remotes automatically
* Very few dependencies: Python, Git, that's it
* Works via the simple Git daemon protocol

### Limitations

* No authentication options available, just like the original Git daemon.
Don't expose this to the Internet!
* Has no locking mechanisms to avoid concurrent operations on the cached git repositories,
apart from what Git may already have.
It's best to avoid cloning / fetching from the same remote repository from multiple clients at the same time.
* Does not support pushing.
Git allows a remote to have different fetch and push URLs,
so it may be possible to set up a remote to fetch from `git-caching-proxy`,
and push to the remote repository directly,
but I have not tested this personally.

### Projects with similar goals

* https://github.com/google/goblet
* https://kooltux.github.io/git-cache/
* https://www.npmjs.com/package/git-cache


## How to use

### Requirements

* Python 3.9 or above
* Git
* Some disk space to store the cache repositories
* The example setup uses `systemd`, but any `inetd`-like super daemon will work

### Setting up the server

This setup uses `systemd`.
If using another `inetd`-like implementation, adjust as required.

1. Choose a server. It can be localhost, or a dedicated server.

2. The server is configured with environment variables.
In the example setup, the variables are defined in `git-caching-daemon.conf`.
Read the comments and edit accordingly.
The provided `systemd` service file will use this file to provide environment variables.

3. Put `git_caching_proxy.py` and `git-caching-daemon.conf` somewhere convenient.
The example setup have them in `/opt/gitcache/`.
Make sure `git_caching_proxy.py` is executable.

4. Edit `git-caching-daemon@.service`.
Specify the correct paths for the files you placed in the previous step.
Also create a dedicated user / group for the service for best practice.
The unit file specifies `gitcache:gitcache`.

5. Place `git-caching-daemon@.service` and `git-caching-daemon@.service` in `/etc/systemd/system`,
and enable the socket with `systemctl enable git-caching-daemon.socket`.
Open Port 9418 on the firewall if access from other hosts is desired.

### Using `git`

TLDR:

Using manually: just add `git://server-hostname/` in front of the real repository address.
For example: `git clone git://server-hostname/https://github.com/twisteroidambassador/git-caching-proxy.git`

Using automatically: something like `git config --global url."git://server-hostname/https://".insteadOf "https://"`

Detailed instructions: *work in progress*