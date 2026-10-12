# Hadoop 3.3.6 Installation and Configuration Guide (Ubuntu 22.04 / WSL2)

This guide documents the exact steps for setting up Hadoop 3.3.6 in pseudo-distributed and multi-node modes.

---

## 1. Prerequisites (Ubuntu 22.04 LTS)

```bash
# Update package list and install OpenJDK 11 and SSH server
sudo apt update
sudo apt install -y openjdk-11-jdk ssh pdsh

# Set up dedicated hadoop user (Optional, or use current user)
sudo useradd -m -s /bin/bash hadoop
sudo usermod -aG sudo hadoop
sudo passwd hadoop

# Generate SSH keys for passwordless localhost access
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 0600 ~/.ssh/authorized_keys
ssh localhost   # Verify no password is required, then type 'exit'
```

---

## 2. Download and Unpack Hadoop 3.3.6

```bash
cd ~
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 /usr/local/hadoop
sudo chown -R $USER:$USER /usr/local/hadoop
```

---

## 3. Environment Variables (`~/.bashrc`)

Add the following to the bottom of `~/.bashrc`:
```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/sbin:$HADOOP_HOME/bin
```
Reload:
```bash
source ~/.bashrc
```

Configure `hadoop-env.sh`:
```bash
# In /usr/local/hadoop/etc/hadoop/hadoop-env.sh:
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

---

## 4. Install Configuration Files

Copy the provided `core-site.xml` and `hdfs-site.xml` into `/usr/local/hadoop/etc/hadoop/`:
```bash
cp core-site.xml /usr/local/hadoop/etc/hadoop/core-site.xml
cp hdfs-site.xml /usr/local/hadoop/etc/hadoop/hdfs-site.xml
```

Create HDFS data folders:
```bash
mkdir -p /home/hadoop/hadoop_data/hdfs/namenode
mkdir -p /home/hadoop/hadoop_data/hdfs/datanode
mkdir -p /home/hadoop/hadoop_data/tmp
```

---

## 5. Format NameNode & Start Daemons

```bash
# Format the NameNode (run ONLY once on initial setup)
hdfs namenode -format

# Start HDFS daemons (NameNode, SecondaryNameNode, DataNode)
start-dfs.sh

# Verify running Java processes
jps
# Expected output:
# NameNode
# DataNode
# SecondaryNameNode
# Jps
```

---

## 6. Prepare MiniCloud Root Directory in HDFS

```bash
# Create base path for MiniCloud
hdfs dfs -mkdir -p /minicloud/users

# Ensure wide permissions for WebHDFS operations
hdfs dfs -chmod -R 777 /minicloud

# Verify structure
hdfs dfs -ls /
```

---

## 7. WebHDFS Check

Open browser or run curl:
- NameNode Web UI: `http://<UBUNTU_IP>:9870`
- WebHDFS check:
```bash
curl "http://<UBUNTU_IP>:9870/webhdfs/v1/minicloud?op=GETFILESTATUS&user.name=hadoop"
```
