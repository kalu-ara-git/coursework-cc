#!/usr/bin/env bash

# This script installs EKS prerequisites

set -e

# Ensure $HOME/bin exists and is in PATH
mkdir -p $HOME/bin
echo 'export PATH=$HOME/bin:$PATH' >>~/.bashrc
source ~/.bashrc

# Install kubectl
if ! type kubectl >/dev/null 2>&1; then
    echo "Installing kubectl..."
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/$(uname -s)/amd64/kubectl"
    chmod +x kubectl
    mv kubectl $HOME/bin/
    echo "kubectl installed."
else
    echo "kubectl already installed."
fi

# Install AWS CLI v2
if ! type aws >/dev/null 2>&1; then
    echo "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    echo "AWS CLI installed."
else
    echo "AWS CLI already installed."
fi

# Install eksctl
if ! type eksctl >/dev/null 2>&1; then
    echo "Installing eksctl..."
    curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
    mv /tmp/eksctl $HOME/bin/
    echo "eksctl installed."
else
    echo "eksctl already installed."
fi

# Install kubectx/kubens
if ! type kubectx >/dev/null 2>&1; then
    echo "Installing kubectx/kubens..."
    sudo git clone https://github.com/ahmetb/kubectx /usr/local/kubectx
    sudo ln -s /usr/local/kubectx/kubectx /usr/local/bin/kubectx
    sudo ln -s /usr/local/kubectx/kubens /usr/local/bin/kubens
    echo "kubectx/kubens installed."
else
    echo "kubectx/kubens already installed."
fi

# Verify AWS credentials
echo "Verifying AWS credentials..."
aws sts get-caller-identity
