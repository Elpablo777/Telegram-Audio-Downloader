# Issue Summary Workflow

This GitHub Actions workflow automatically generates summaries for new issues when they are opened.

## Features

- Automatically creates a summary comment on new issues
- Uses OpenAI GPT for intelligent summarization (when configured)
- Falls back to basic summarization if OpenAI is not configured or available
- Works completely automatically without manual intervention

## How It Works

When a new issue is opened, the workflow:

1. Extracts the issue title and body
2. If an OpenAI API key is configured, sends the issue content to OpenAI for intelligent summarization
3. If OpenAI is not configured or fails, creates a basic summary with the first 500 characters
4. Adds the summary as a comment to the issue

## Configuration

### OpenAI Integration (Optional)

To enable intelligent summarization with OpenAI:

1. Get an OpenAI API key from [OpenAI](https://platform.openai.com/)
2. Add the API key as a secret in your repository:
   - Go to Settings > Secrets and variables > Actions
   - Click "New repository secret"
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key
3. The workflow will automatically use OpenAI when the secret is available

### Without OpenAI

If you don't configure an OpenAI API key, the workflow will still work but will create a basic summary with the first 500 characters of the issue body.

## Customization

You can customize the workflow by modifying the `issue-summary.yml` file:

- Change the OpenAI model by modifying the `model` parameter (default: `gpt-3.5-turbo`)
- Adjust the maximum tokens for the summary by changing `max_tokens` (default: `300`)
- Modify the prompt used for summarization by editing the system message

## Privacy

The workflow only processes publicly available issue content. If you use the OpenAI integration:

- Issue content is sent to OpenAI's API for processing
- OpenAI's privacy policy applies to this data
- No other data is sent to third parties
- You can disable the OpenAI integration by removing the `OPENAI_API_KEY` secret

## Troubleshooting

If the workflow is not working:

1. Check that the workflow file is in the correct location (`.github/workflows/issue-summary.yml`)
2. Verify that the repository has the necessary permissions for the workflow
3. Check the workflow run logs for any error messages
4. Ensure that the `issues: write` permission is granted in the workflow

If you have any issues or questions, please open an issue in the repository.