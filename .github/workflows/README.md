# GitHub Actions Workflows

This directory contains various GitHub Actions workflows that automate different aspects of the repository management.

## Workflows

### Issue Summary (`issue-summary.yml`)

Automatically generates a summary for new issues when they are opened. Features include:
- Intelligent summarization using OpenAI GPT (when configured)
- Fallback to basic summarization without external dependencies
- Automatic commenting on new issues with the generated summary

For detailed information about configuration and customization, see [ISSUE_SUMMARY.md](ISSUE_SUMMARY.md).

## Setup

All workflows are automatically enabled when pushed to the repository. No additional setup is required.

For the Issue Summary workflow with OpenAI integration:
1. Get an OpenAI API key from [OpenAI](https://platform.openai.com/)
2. Add it as a secret named `OPENAI_API_KEY` in your repository settings

## Customization

You can customize the workflows by modifying the `.yml` files in this directory. Each workflow file contains detailed comments explaining its functionality.