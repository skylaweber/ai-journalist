# AI-Journalist
[![Twitter Follow](https://img.shields.io/twitter/follow/mattshumer_?style=social)](https://twitter.com/mattshumer_)

# Claude-Journalist | An experimental AI-powered journalist

Claude-Journalist leverages the power of the Claude 3 AI model to research, write, and edit high-quality articles on any given topic. It utilizes web search APIs to gather relevant information, analyzes the content, and generates well-structured, informative, and engaging articles that read as if they could be published in major media publications.

## Try it without code!
If you want to try the AI journalist, but don't want to bother with code, you can use a modified version directly on the [HyperWrite Platform](https://app.hyperwriteai.com/personalassistant/tool/183607bc-a92d-4d7b-9b7d-358b4758b2c0). If you're a first-time user, you will be asked to sign in. Once you do so, come back and click this link again to go directly to the tool.

## Workflow

The script guides the user through the following process:
1.  **Topic Input:** Prompts the user to enter a topic to write about.
2.  **LLM Model Selection:** Prompts the user to choose an Anthropic LLM model (Haiku, Sonnet, or Opus) to be used for generation and editing tasks.
3.  **Search Provider Selection:** Prompts the user to choose a search provider (SERP API or Brave Search).
4.  **Initial Search Term Generation:** Generates a list of initial search terms related to the topic using the selected Anthropic LLM.
5.  **Web Search:** Performs searches using the chosen provider (SERP API or Brave Search) for each search term.
6.  **URL Selection:** The LLM selects the most relevant and informative URLs from the combined search results.
7.  **Content Extraction:** Retrieves article text from the selected URLs using the `newspaper3k` library.
8.  **Initial Article Generation:** The LLM writes a high-quality article based on the retrieved article texts.
9.  **Refinement Loop (Optional):**
    *   Asks the user if they want to provide follow-up questions or feedback.
    *   If yes, the user provides their input.
    *   The LLM generates new search terms based on this feedback.
    *   Additional web searches are performed, new relevant articles are fetched and processed.
    *   The LLM refines the original article by incorporating the user's feedback and any new information gathered.
10. **Final AI Edit Pass (Optional):**
    *   Asks the user if they want an AI to perform an additional editing pass on the (potentially refined) article.
    *   If yes, the LLM reviews and rewrites the article for clarity, coherence, and overall quality.
11. **Output:** Prints the generated/refined article and, if applicable, the final AI-edited version.
12. **Source URLs:** Lists all unique source URLs that were used to gather information for the article.

## Requirements

To run AI-Journalist, you need:
- Python 3.x
- An Anthropic API key for accessing the Claude AI models. Set this as an environment variable: `ANTHROPIC_API_KEY`.
- An API key for your chosen search provider:
    - For SERP API: `SERP_API_KEY`
    - For Brave Search: `BRAVE_SEARCH_API_KEY`
    - You need to set the environment variable for at least the service you intend to use. You can set both if you wish to switch between them.
- Python packages as listed in `requirements.txt`. Install them using:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

1.  Ensure you have set the required environment variables (see Requirements section).
2.  Navigate to the project directory in your terminal.
3.  Run the script using:
    ```bash
    python ai_journalist.py
    ```
4.  Follow the prompts:
    *   Enter the topic for the article.
    *   Choose your preferred Anthropic LLM model.
    *   Select your search provider (serpapi or brave).
    *   Decide if you want to engage in the follow-up/refinement loop.
    *   Decide if you want a final AI editing pass.
5.  Wait for the AI system to research, write, (potentially) refine, and edit the article. The final article(s) and source URLs will be printed to the console.

## Disclaimer

Claude-Journalist is an experimental tool designed to assist in the article writing process. While it aims to generate high-quality content, the output should be carefully reviewed and fact-checked by human editors before any publication. The generated articles may require further editing and refinement to meet specific editorial standards and guidelines.

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

Some known improvement areas:
- **Search Provider Expansion:** Integrate more search APIs or allow for direct URL input. Brave Search integration is currently a proof-of-concept.
- **Enhanced Fact-Checking:** While the LLM aims for accuracy, integrating more robust, external fact-checking mechanisms would be beneficial.
- **User Interface:** A simple web UI or a more interactive CLI could improve usability.
- **Modularity:** Further refactor the code for better modularity and easier extension.
- **Error Handling:** Continue to improve error handling for API calls and external library interactions.
- **Custom Prompts:** Allow users to customize the prompts used for different LLM tasks.

## Contact

Matt Shumer - [@mattshumer_](https://twitter.com/mattshumer_)

Lastly, if you want to try something even cooler than this, sign up for [HyperWrite Personal Assistant](https://app.hyperwriteai.com/personalassistant). It's basically an AI with access to real-time information that a) is incredible at writing naturally, and b) can operate your web browser to complete tasks for you.
<!-- Test commit to main branch -->
