# luks-webui
A simple Flask web interface to manage LUKS encrypted disks

## Installation

1. Download filebrowser and place the binary in `/opt/filebrowser/`
2. Download the file `filebrowser.service` and place it in `/etc/systemd/system/`
3. Download the file `diskui.service` and place it in `/etc/systemd/system/`
4. Start the services:
```bash
systemctl daemon-reload
systemctl enable diskui.service
systemctl start diskui.service
```

We don't start the filebrowser service automatically, as it is started by the diskui service when needed.

## Setup luks encrypted disk

1. Identify the Disk
List available disks:
    ```bash
    lsblk
    ```

2. Format with LUKS
Initialize the disk with LUKS encryption:
    ```bash
    sudo cryptsetup luksFormat /dev/sda
    ```

3. Open the Encrypted Disk
Unlock and map it to a device name (e.g., `secure_storage`):
    ```bash
    sudo cryptsetup luksOpen /dev/sda secure_storage
    ```

4. Format the mapped device with EXT4:
    ```bash
    sudo mkfs.ext4 /dev/mapper/secure_storage
    ```

5. Create a mount point and mount the encrypted volume:
    ```bash
    sudo mkdir -p /mnt/secure
    sudo mount /dev/mapper/secure_storage /mnt/secure
    ```

6. Verify
    ```bash
    lsblk
    ```