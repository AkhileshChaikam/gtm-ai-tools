# Vibe coding new workflows

This project uses the OpenAI Codex CLI to scaffold new utilities.
The CLI runs locally, outside the Docker container.

1. Install **Node.js 22+** and the CLI. Run the helper task or follow the
   [install_node.md](install_node.md) guide:
   ```bash
   task setup:codex
   ```
2. Generate a script from the project root. The `task add_utility` command runs
   the Codex CLI in quiet mode with automatic approval:
   ```bash
   task add_utility -- search_vp_sales "search for VP of sales and push to Dhisana Webhook"
   ```
3. Work on a branch, then commit and push the changes:
   ```bash
   git checkout -b my-feature
   git commit -am "Add my tool"
   git push origin my-feature
   ```

4. Rebuild the Docker image and start the web app to access your new utility.

## Example workflow ideas

- Find people by job title at a company.
- Look up people by name and keywords.
- Scrape a custom website for leads.
- Use an LLM to research and summarize a company.
