# git-caching-proxy
Speed up repeated git clones / fetches and reduce network traffic

## What is this?

The name is very straightforward: this is a caching proxy server for Git.

Once set up, the proxy server will maintain an up-to-date copy of any remote repositories you clone / fetch through it.
This means cloning the same repository repeatedly will use much less network traffic, and as a result be much faster.
A lot of time will be saved if, for example, you have a `RUN git clone ...` command in your Dockerfile.

### Advantages

* Uses the original `git` commands
* Can `git config` to use for all or some remotes automatically
* Works via the simple Git daemon protocol

### Projects with similar goals

* https://github.com/google/goblet
* https://kooltux.github.io/git-cache/
* https://www.npmjs.com/package/git-cache


## How to use

### Requirements

* Python 3.9 or above
* Git

### Setting up the server

TLDR: edit the `.conf` file, put the `.py` and `.conf` files somewhere convenient,
edit the `.server` file according to the paths of the `.py` and `.conf` files,
put the `.socket` and `.server` files in `/etc/systemd/system`,
run `systemctl enable git-caching-daemon.socket`,
open port 9418 on firewall.

Detailed instructions: *work in progress*

### Using `git`

TLDR:

Using manually: just add `git://server-hostname/` in front of the real repository address.
For example: `git clone git://server-hostname/https://github.com/twisteroidambassador/git-caching-proxy.git`

Using automatically: something like `git config --global url."git://server-hostname/https://".insteadOf "https://"`

Detailed instructions: *work in progress*