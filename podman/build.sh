#!/bin/bash

# Prompt the user if they want to enter GitHub details
read -p "Do you want to enter your GitHub details? (y/n): " ENTER_GITHUB

if [[ $ENTER_GITHUB =~ ^[Yy]$ ]]; then
  # Prompt the user for input
  read -p "Enter your GitHub username: " GITHUB_USERNAME
  read -p "Enter your GitHub email: " GITHUB_EMAIL
  read -p "Enter the path to your GitHub private key: " GITHUB_PRIVATE_KEY_PATH

  # Read the contents of the private key file
  GITHUB_PRIVATE_KEY=$(cat "$GITHUB_PRIVATE_KEY_PATH")

  # Build the Occam machine image with the provided values
  podman build -t occam_local \
    --build-arg GITHUB_USERNAME="$GITHUB_USERNAME" \
    --build-arg GITHUB_EMAIL="$GITHUB_EMAIL" \
    --build-arg GITHUB_PRIVATE_KEY="$GITHUB_PRIVATE_KEY" .
else
  # Build the Occam machine image without GitHub details
  podman build -t occam_local .
fi
