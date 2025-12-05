import json
from llm.client import GeminiClient

class ConceptMatcher:
    def __init__(self):
        self.client = GeminiClient()

    def _clean_json_response(self, response: str) -> str:
        """Remove markdown code fences from LLM JSON responses"""
        clean = response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return clean.strip()

    def extract_concepts(self, user_description: str, image_base64: str = None) -> dict:
        """Extract searchable concepts from user's idea (and optional image)"""
        
        prompt_intro = "Extract key concepts from this product idea for searching."
        if image_base64:
            prompt_intro += " I have provided an image of the concept along with the description. Use visual details from the image (materials, shape, mechanism) to enhance the search keywords."

        prompt = f"""
{prompt_intro}

Crucial: Identify "Negative Keywords". These are terms that often appear in similar BUT WRONG contexts.
For example:
- If idea is "Cat Sleep Collar", negative keywords: ["dog", "bark", "training", "shock"] (to avoid dog collars or shock collars)
- If idea is "Surfboard Lamp", negative keywords: ["wax", "leash", "fin", "repair"] (to avoid surfboard accessories)

Idea Description: {user_description}

Return JSON with:
- core_function: what it does
- key_features: unique attributes
- search_keywords: 5 search terms
- negative_keywords: list of excluded terms
- category: product category

JSON only, no explanation.
"""
        response = self.client.generate(prompt, image_base64=image_base64)
        return json.loads(self._clean_json_response(response))

    def filter_noise(self, results: list[dict], negative_keywords: list[str]) -> list[dict]:
        """
        Filter out results that contain negative keywords in their title.
        This acts as a 'Quick Kill' to remove obvious false positives before expensive LLM processing.
        """
        if not negative_keywords:
            return results

        clean_results = []
        
        # Normalize negative keywords for case-insensitive matching
        normalized_negatives = [nk.lower().strip() for nk in negative_keywords]

        for item in results:
            # Check Name (Title) - Primary filter
            name = item.get('name', '').lower()
            
            # Check Description - Secondary filter (if available, be careful not to filter too aggressively)
            # For now, let's stick to Title filtering to avoid false negatives if a description mentions "not for dogs"
            
            is_noise = False
            for neg in normalized_negatives:
                # Word boundary check is better, but simple substring is robust for MVP
                if neg in name:
                    is_noise = True
                    break
            
            if not is_noise:
                clean_results.append(item)

        return clean_results

    def calculate_similarity(self, user_idea: str, competitor_product: dict) -> dict:
        """
        Compare user's idea to found product
        Returns: {score: 0-100, reasoning: str}
        """
        prompt = f"""
Compare this invention idea to an existing product:

USER'S IDEA:
{user_idea}

EXISTING PRODUCT:
Name: {competitor_product.get('name', 'N/A')}
Description: {competitor_product.get('description', 'N/A')}
Price: {competitor_product.get('price', 'N/A')}

Respond with JSON:
{{
  "score": <0-100 similarity percentage>,
  "reasoning": "<why they are/aren't similar>",
  "user_advantage": "<what makes user's idea unique, if anything>"
}}

JSON only.
"""
        response = self.client.generate(prompt)
        return json.loads(self._clean_json_response(response))

    def generate_verdict(self, user_idea: str, competitors: list[dict]) -> str:
        """
        Generate a 1-sentence GO/NO-GO verdict based on the found competitors.
        """
        competitor_summary = "\n".join([
            f"- {c['product_name']} ({c['similarity_score']}% match)" 
            for c in competitors[:5]
        ])

        prompt = f"""
Act as a brutal startup advisor. Based on the user's idea and the competitors found, give a 1-sentence verdict.

User Idea: {user_idea}

Found Competitors:
{competitor_summary}

Task:
- If high similarity (>80%) matches exist: Recommend PIVOT or STOP.
- If only low similarity exists: Recommend PROCEED but CAUTIOUSLY.
- If no real competitors: Recommend GO FOR IT.

Output ONE sentence only. Start with "Verdict:".
        """
        return self.client.generate(prompt).strip()

    def analyze_gaps(self, user_idea: str, competitor_name: str, complaints: list[str]) -> str:
        """
        Analyze competitor complaints and identify the market gap for the user's idea.
        """
        complaints_text = "\n".join([f"- {c}" for c in complaints[:10]])

        prompt = f"""
Market Gap Analysis:

User's Idea: {user_idea}
Competitor Product: {competitor_name}

Public Complaints Found about Competitor:
{complaints_text}

Task:
1. Identify the top 2-3 recurring problems/pain points from the complaints.
2. Explain how the User's Idea solves (or fails to solve) these specific problems.
3. Provide a "Marketing Hook" based on this gap.

Output plain text, max 3 sentences.
Format:
"Competitors suffer from [Problem]. Your idea [Solves/Doesn't Solve] this by [Feature]. Opportunity: [Marketing Hook]."
"""
        return self.client.generate(prompt).strip()
