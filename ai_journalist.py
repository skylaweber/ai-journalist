#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article
import ast
import os
import json

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SERP_API_KEY = os.environ.get("SERP_API_KEY")
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY")

AVAILABLE_MODELS = {
    "Haiku": "claude-3-haiku-20240307",
    "Sonnet": "claude-3-sonnet-20240229",
    "Opus": "claude-3-opus-20240229"
}

def get_search_terms(topic, model_name):
    system_prompt = "You are a world-class journalist. Generate a list of 5 search terms to search for to research and write an article about the topic."
    messages = [
        {"role": "user", "content": f"Please provide a list of 5 search terms related to '{topic}' for researching and writing an article. Respond with the search terms in a Python-parseable list, separated by commas."},
    ]
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model_name,
        "max_tokens": 200,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": messages,
    }

    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    response_text = response.json()['content'][0]['text']
    search_terms = ast.literal_eval(response_text)
    return search_terms

def get_search_results(search_term): # Default to SERP API
    if not SERP_API_KEY:
        print("SERP_API_KEY is not set. Please set this environment variable to use SerpAPI.")
        return []
    url = f"https://serpapi.com/search.json?q={search_term}&api_key={SERP_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('organic_results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error during SERP API request: {e}")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON response from SERP API.")
        return []

def get_brave_search_results(search_term, api_key):
    if not api_key: # This check is now redundant due to main block check, but good for direct calls
        print("Brave Search API key is missing. Please set the BRAVE_SEARCH_API_KEY environment variable.")
        return []
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "X-Subscription-Token": api_key,
        "Accept": "application/json"
    }
    params = {"q": search_term}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get('web', {}).get('results', [])
        transformed_results = []
        for result in results:
            transformed_results.append({
                'link': result.get('url'),
                'title': result.get('title'),
                'snippet': result.get('description')
            })
        return transformed_results
    except requests.exceptions.RequestException as e:
        print(f"Error during Brave Search API request: {e}")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON response from Brave Search API.")
        return []

def select_relevant_urls(search_results, model_name):
    system_prompt = "You are a journalist assistant. From the given search results, select the URLs that seem most relevant and informative for writing an article on the topic."
    search_results_text = "\n".join([f"{i+1}. {result.get('link', 'N/A')}: {result.get('title', 'N/A')}" for i, result in enumerate(search_results)])
    messages = [
        {"role": "user", "content": f"Search Results:\n{search_results_text}\n\nPlease select the numbers of the URLs that seem most relevant and informative for writing an article on the topic. Respond with the numbers in a Python-parseable list, separated by commas."},
    ]
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model_name,
        "max_tokens": 200,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": messages,
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()
        response_text = response.json()['content'][0]['text']
        numbers = ast.literal_eval(response_text)
        relevant_indices = [int(num) - 1 for num in numbers]
        # Ensure indices are within bounds
        relevant_urls = [search_results[i]['link'] for i in relevant_indices if 0 <= i < len(search_results)]
        return relevant_urls
    except requests.exceptions.RequestException as e:
        print(f"Error during Anthropic API request for URL selection: {e}")
        return []
    except ast.literal_eval as e:
        print(f"Error parsing URL selection from LLM response: {e}. Response was: {response_text if 'response_text' in locals() else 'N/A'}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in select_relevant_urls: {e}")
        return []


def get_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        print(f"Error fetching or parsing article from {url}: {e}")
        return ""

def write_article(topic, article_texts, model_name):
    system_prompt = "You are a journalist. Write a high-quality, NYT-worthy article on the given topic based on the provided article texts. The article should be well-structured, informative, and engaging."
    combined_text = "\n\n".join(article_texts)
    messages = [
        {"role": "user", "content": f"Topic: {topic}\n\nArticle Texts:\n{combined_text}\n\nPlease write a high-quality, NYT-worthy article on the topic based on the provided article texts. The article should be well-structured, informative, and engaging. Ensure the length is at least as long as a NYT cover story -- at a minimum, 15 paragraphs."},
    ]
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model_name,
        "max_tokens": 3000,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": messages,
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()
        article = response.json()['content'][0]['text']
        return article
    except requests.exceptions.RequestException as e:
        print(f"Error during Anthropic API request for writing article: {e}")
        return "Error: Could not generate article."
    except Exception as e:
        print(f"An unexpected error occurred in write_article: {e}")
        return "Error: Could not generate article due to an unexpected issue."

def edit_article(article, model_name):
    system_prompt_suggestions = "You are an editor. Review the given article and provide suggestions for improvement. Focus on clarity, coherence, and overall quality."
    messages_suggestions = [
        {"role": "user", "content": f"Article:\n{article}\n\nPlease review the article and provide suggestions for improvement. Focus on clarity, coherence, and overall quality."},
    ]
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data_suggestions = {
        "model": model_name,
        "max_tokens": 3000,
        "temperature": 0.5,
        "system": system_prompt_suggestions,
        "messages": messages_suggestions,
    }
    try:
        response_suggestions = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data_suggestions)
        response_suggestions.raise_for_status()
        suggestions = response_suggestions.json()['content'][0]['text']

        system_prompt_rewrite = "You are an editor. Rewrite the given article based on the provided suggestions for improvement."
        messages_rewrite = [
            {"role": "user", "content": f"Original Article:\n{article}\n\nSuggestions for Improvement:\\n{suggestions}\\n\\nPlease rewrite the article based on the provided suggestions for improvement."},
        ]
        data_rewrite = {
            "model": model_name,
            "max_tokens": 3000, # Max tokens for the edited article
            "temperature": 0.5,
            "system": system_prompt_rewrite,
            "messages": messages_rewrite,
        }
        response_rewrite = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data_rewrite)
        response_rewrite.raise_for_status()
        edited_article = response_rewrite.json()['content'][0]['text']
        return edited_article
    except requests.exceptions.RequestException as e:
        print(f"Error during Anthropic API request in edit_article: {e}")
        return article # Return original article if editing fails
    except Exception as e:
        print(f"An unexpected error occurred in edit_article: {e}")
        return article


def get_refinement_search_terms(original_topic, user_feedback, model_name):
    system_prompt = f"You are a research assistant. The user is working on an article about '{original_topic}'. They have provided the following feedback or questions: '{user_feedback}'. Generate a list of 3-5 new search terms to find information that would help address this feedback and refine the article. Respond with the search terms in a Python-parseable list."
    messages = [
        {"role": "user", "content": "Please provide the list of new search terms."},
    ]
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model_name,
        "max_tokens": 150,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": messages,
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()
        response_text = response.json()['content'][0]['text']
        search_terms = ast.literal_eval(response_text)
        return search_terms
    except requests.exceptions.RequestException as e:
        print(f"Error during Anthropic API request for refinement search terms: {e}")
        return []
    except ast.literal_eval as e:
        print(f"Error parsing refinement search terms from LLM response: {e}. Response was: {response_text if 'response_text' in locals() else 'N/A'}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in get_refinement_search_terms: {e}")
        return []

def refine_article(original_article, user_feedback, new_article_texts, model_name):
    system_prompt = "You are a journalist. You have written an article. The user has provided feedback/questions, and you have gathered additional information. Please rewrite and improve the original article to incorporate the feedback and utilize the new information. Ensure the refined article is comprehensive and addresses the user's points. If new_article_texts is empty, refine based on feedback alone."
    combined_new_texts = "\n\n".join(new_article_texts) if new_article_texts else "No new specific articles were found for this refinement."

    content = f"Original Article:\n{original_article}\n\nUser Feedback/Questions:\n{user_feedback}\n\nAdditional Information Gathered:\n{combined_new_texts}\n\nPlease rewrite the original article incorporating all of the above."

    messages = [{"role": "user", "content": content}]
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model_name,
        "max_tokens": 4000,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": messages,
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()
        refined_article = response.json()['content'][0]['text']
        return refined_article
    except requests.exceptions.RequestException as e:
        print(f"Error during Anthropic API request for article refinement: {e}")
        return original_article
    except Exception as e:
        print(f"An unexpected error occurred in refine_article: {e}")
        return original_article


if __name__ == "__main__":
    topic = input("Enter a topic to write about: ")

    print("\nAvailable Anthropic LLM Models:")
    for key, value in AVAILABLE_MODELS.items():
        print(f"- {key} ({value})")
    selected_model_key = None
    while selected_model_key not in AVAILABLE_MODELS:
        selected_model_key = input(f"Please select a model (enter the key e.g., Haiku, Sonnet, Opus): ")
        if selected_model_key not in AVAILABLE_MODELS:
            print("Invalid selection. Please choose from the available models.")
    selected_model_name = AVAILABLE_MODELS[selected_model_key]
    print(f"You selected: {selected_model_key} ({selected_model_name})")

    search_provider = None
    while search_provider not in ['serpapi', 'brave']:
        search_provider = input("Select search provider ('serpapi' or 'brave'): ").lower()
        if search_provider not in ['serpapi', 'brave']:
            print("Invalid selection. Please choose 'serpapi' or 'brave'.")

    if search_provider == 'serpapi' and not SERP_API_KEY:
        print("SERP_API_KEY is not set. Please set this environment variable to use SerpAPI. Exiting.")
        exit()
    elif search_provider == 'brave' and not BRAVE_SEARCH_API_KEY:
        print("BRAVE_SEARCH_API_KEY is not set. Please set this environment variable to use Brave Search. Exiting.")
        exit()
    print(f"Using {search_provider} for searches.")

    search_terms_model = selected_model_name
    url_selection_model = selected_model_name
    writing_model = selected_model_name
    editing_model = selected_model_name

    print("\nGenerating initial search terms...")
    search_terms = get_search_terms(topic, search_terms_model)
    print(f"Initial Search Terms for '{topic}': {', '.join(search_terms)}")

    relevant_urls = []
    all_search_results_for_url_selection = []
    if search_terms:
        for term in search_terms:
            print(f"\nSearching for: {term} using {search_provider}...")
            if search_provider == 'serpapi':
                current_search_results = get_search_results(term)
            else:
                current_search_results = get_brave_search_results(term, BRAVE_SEARCH_API_KEY)

            if current_search_results:
                all_search_results_for_url_selection.extend(current_search_results)
            else:
                print(f"No results found for '{term}'.")

        if all_search_results_for_url_selection:
            print("\nSelecting relevant URLs from combined search results...")
            unique_results_by_link = {res['link']: res for res in all_search_results_for_url_selection if res.get('link')}.values()
            urls = select_relevant_urls(list(unique_results_by_link), url_selection_model)
            relevant_urls.extend(urls)
        else:
            print("No search results obtained to select URLs from.")
    else:
        print("No initial search terms were generated.")

    print('\nRelevant URLs to read:', relevant_urls)

    article_texts = []
    if relevant_urls:
        print("\nFetching article texts from relevant URLs...")
        for url in relevant_urls:
            text = get_article_text(url)
            if text and len(text) > 75:
                article_texts.append(text)
        print(f"Successfully fetched text from {len(article_texts)} URLs.")
    else:
        print("No relevant URLs to fetch text from.")

    if not article_texts:
        print("\nNo article texts gathered. Cannot write an article.")
        article = "Could not generate an article as no source text was successfully retrieved."
    else:
        print('\n\nWriting article...')
        article = write_article(topic, article_texts, writing_model)

    print("\n--- Generated Article ---")
    print(article)
    print("--- End of Generated Article ---")

    ask_for_refinement = input("\nDo you want to refine the article with follow-up questions or feedback? (yes/no): ").lower()
    if ask_for_refinement == 'yes':
        user_feedback = input("Please provide your follow-up questions or feedback: ")

        print("\nGenerating search terms for refinement based on your feedback...")
        refinement_search_terms = get_refinement_search_terms(topic, user_feedback, search_terms_model)

        new_article_texts = []
        newly_fetched_urls_for_refinement = []

        if refinement_search_terms:
            print(f"New search terms for refinement: {', '.join(refinement_search_terms)}")
            all_refinement_search_results = []
            for term in refinement_search_terms:
                print(f"\nSearching for (refinement): {term} using {search_provider}...")
                if search_provider == 'serpapi':
                    current_refinement_results = get_search_results(term)
                else:
                    current_refinement_results = get_brave_search_results(term, BRAVE_SEARCH_API_KEY)

                if current_refinement_results:
                    all_refinement_search_results.extend(current_refinement_results)
                else:
                    print(f"No results found for refinement term '{term}'.")

            if all_refinement_search_results:
                print("\nSelecting relevant URLs from refinement search results...")
                unique_refinement_results = {res['link']: res for res in all_refinement_search_results if res.get('link')}.values()
                selected_refinement_urls = select_relevant_urls(list(unique_refinement_results), url_selection_model)
                print(f"Selected URLs for refinement: {', '.join(selected_refinement_urls)}")

                print("\nFetching article texts for refinement...")
                for url in selected_refinement_urls:
                    if url not in relevant_urls:
                        text = get_article_text(url)
                        if text and len(text) > 75:
                            new_article_texts.append(text)
                            newly_fetched_urls_for_refinement.append(url)
                    else:
                        print(f"Skipping already processed URL: {url}")

                if new_article_texts:
                    print(f"\nFetched text from {len(new_article_texts)} new articles for refinement.")
                else:
                    print("\nNo new article texts were fetched for refinement.")
            else:
                print("No search results obtained for refinement terms.")
        else:
            print("No refinement search terms were generated.")

        print("\nRefining the article based on your feedback and new information (if any)...")
        article = refine_article(article, user_feedback, new_article_texts, writing_model)
        print("\n--- Refined Article ---")
        print(article)
        print("--- End of Refined Article ---")

        relevant_urls.extend(newly_fetched_urls_for_refinement)
        relevant_urls = list(dict.fromkeys(relevant_urls)) # Deduplicate

    do_edit = input("\nAfter reviewing the article, do you want an automatic AI edit pass? (yes/no): ").lower()
    if 'y' in do_edit:
      print("\nPerforming final AI edit pass...")
      article = edit_article(article, editing_model)
      print("\n--- Final Edited Article ---")
      print(article)
      print("--- End of Final Edited Article ---")
    else:
      print("\n--- Final Article (No AI Edit Pass) ---")
      print(article)
      print("--- End of Final Article ---")

    print("\nSources Used:")
    if relevant_urls:
        for url in relevant_urls:
            print(f"- {url}")
    else:
        print("No sources were used for this article (or no URLs were successfully processed).")
