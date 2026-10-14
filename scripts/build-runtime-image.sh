#!/usr/bin/env bash
# Run on a disposable Linux image builder with sudo. No Android root is used.
set -euo pipefail
distro=${1:?debian or ubuntu};out=${2:?output directory}
root=$(cd "$(dirname "$0")/.." && pwd)
out=$(realpath -m "$out");mkdir -p "$out"
work=$(mktemp -d);guest="$work/rootfs"
trap 'sudo umount "$guest/proc" 2>/dev/null || true; sudo rm -rf "$work"' EXIT
case $distro in
 debian) suite=trixie;mirror=https://deb.debian.org/debian;key="$root/runtime/trust/debian-archive-keyring.gpg";kernel=linux-image-arm64;;
 ubuntu) suite=noble;mirror=https://ports.ubuntu.com/ubuntu-ports;key=/usr/share/keyrings/ubuntu-archive-keyring.gpg;kernel=linux-image-generic;;
 *) exit 2;;
esac
sudo debootstrap --foreign --arch=arm64 --variant=minbase --include=ca-certificates --keyring="$key" "$suite" "$guest" "$mirror"
sudo install -m 755 /usr/bin/qemu-aarch64-static "$guest/usr/bin/"
sudo chroot "$guest" /debootstrap/debootstrap --second-stage
sudo mount -t proc proc "$guest/proc"
if [[ $distro == ubuntu ]];then
 printf 'deb https://ports.ubuntu.com/ubuntu-ports noble main universe\ndeb https://ports.ubuntu.com/ubuntu-ports noble-updates main universe\ndeb https://ports.ubuntu.com/ubuntu-ports noble-security main universe\n' | sudo tee "$guest/etc/apt/sources.list" >/dev/null
fi
sudo chroot "$guest" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get -o APT::Update::Error-Mode=any update
sudo chroot "$guest" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $kernel systemd-sysv initramfs-tools openssh-server sudo dbus python3 python3-venv python3-pip python3-cryptography nodejs npm git curl openssh-client iproute2 procps locales
sudo install -d "$guest/etc/systemd/network"
cat <<'NETWORK' | sudo tee "$guest/etc/systemd/network/20-binux.network" >/dev/null
[Match]
Name=eth0
[Network]
Address=10.0.2.15/24
Gateway=10.0.2.2
DNS=10.0.2.3
NETWORK
printf 'nameserver 10.0.2.3\n' | sudo tee "$guest/etc/resolv.conf" >/dev/null
sudo chroot "$guest" systemctl enable systemd-networkd.service
sudo chroot "$guest" useradd -m -s /bin/bash binux
# A locked password prevents PAM account login even with public keys. No usable password.
sudo chroot "$guest" usermod -p '*' binux
printf 'binux ALL=(ALL) NOPASSWD:ALL\n' | sudo tee "$guest/etc/sudoers.d/binux" >/dev/null
sudo chmod 440 "$guest/etc/sudoers.d/binux"
sudo install -d "$guest/etc/binux" "$guest/etc/ssh/sshd_config.d" "$guest/usr/local/lib/binux"
sudo install -m 755 "$root/runtime/guest/binux-first-boot" "$guest/usr/local/sbin/"
for script in binux-entry pkg binux-pip;do sudo install -m 755 "$root/runtime/guest/$script" "$guest/usr/local/bin/";done
sudo ln -s binux-pip "$guest/usr/local/bin/pip"
sudo ln -s binux-pip "$guest/usr/local/bin/pip3"
sudo install -m 644 "$root/runtime/guest/bashrc" "$guest/etc/binux/bashrc"
sudo cp -a "$root/core/binux" "$guest/usr/local/lib/binux/"
printf '#!/bin/sh\nexport PYTHONPATH=/run/binux-bootstrap/core:/usr/local/lib/binux\nexec python3 -m binux.cli "$@"\n' | sudo tee "$guest/usr/local/bin/binux" >/dev/null
printf '#!/bin/sh\nexport PYTHONPATH=/run/binux-bootstrap/core:/usr/local/lib/binux\nexec python3 -m binux.wbs "$@"\n' | sudo tee "$guest/usr/local/bin/wbs" >/dev/null
sudo chmod 755 "$guest/usr/local/bin/binux" "$guest/usr/local/bin/wbs"
sudo install -m 755 "$root/setup-binux-desktop" "$guest/usr/local/bin/setup-binux-desktop"
cat <<'SSH' | sudo tee "$guest/etc/ssh/sshd_config.d/00-binux.conf" >/dev/null
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
AllowUsers binux
AuthorizedKeysFile /etc/binux/authorized/%u
HostKey /etc/ssh/ssh_host_ed25519_key
AllowTcpForwarding local
GatewayPorts no
X11Forwarding no
SSH
cat <<'SERVICE' | sudo tee "$guest/etc/systemd/system/binux-bootstrap.service" >/dev/null
[Unit]
Description=binux VM public-key bootstrap and local shared directories
After=local-fs.target
Before=ssh.service sshd.service
[Service]
Type=oneshot
ExecStart=/usr/local/sbin/binux-first-boot
RemainAfterExit=yes
StandardOutput=journal+console
StandardError=journal+console
[Install]
WantedBy=multi-user.target
SERVICE
printf 'binux-bootstrap /run/binux-bootstrap 9p trans=virtio,version=9p2000.L,ro 0 0\n' | sudo tee -a "$guest/etc/fstab" >/dev/null
sudo chroot "$guest" systemctl enable binux-bootstrap.service ssh.service
sudo chroot "$guest" systemctl mask serial-getty@ttyAMA0.service
# virtio PCI / 9p / ext4 must be available before mounting the root filesystem.
printf 'virtio_pci\nvirtio_blk\nvirtio_net\n9pnet_virtio\n9p\n' | sudo tee -a "$guest/etc/initramfs-tools/modules" >/dev/null
sudo chroot "$guest" update-initramfs -u -k all
sudo chroot "$guest" /bin/bash -c 'python3 -c "import cryptography";node -e "console.log(process.version)";python3 --version;apt-get --version | head -1'
# Record exact package/source versions for reproducibility and GPL source retrieval.
sudo chroot "$guest" dpkg-query -W '-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\n' > "$out/$distro-packages.tsv"
sudo cp -L "$guest"/boot/vmlinuz-* "$out/$distro-kernel"
sudo cp -L "$guest"/boot/initrd.img-* "$out/$distro-initrd"
sudo rm -f "$guest/etc/ssh/ssh_host_"* "$guest/usr/bin/qemu-aarch64-static" "$guest/var/lib/dbus/machine-id"
sudo truncate -s 0 "$guest/etc/machine-id"
sudo chroot "$guest" apt-get clean
sudo umount "$guest/proc"
truncate -s 10G "$work/disk.raw"
sudo mkfs.ext4 -q -F -L binux -d "$guest" "$work/disk.raw"
qemu-img convert -c -O qcow2 "$work/disk.raw" "$out/$distro-disk.qcow2"
sudo chown -R "$(id -u):$(id -g)" "$out"
