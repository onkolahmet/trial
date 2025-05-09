"""
User matching module that implements fuzzy matching logic for Task 1.
"""
from typing import List, Dict
from fuzzywuzzy import fuzz
import re, unicodedata

class UserMatcher:
    """Class that matches transaction descriptions to users based on name similarity."""
    
    def __init__(self, users_data: Dict):
        """Initialize with user data and preprocess names."""
        self.users_data = users_data
        self.user_names = {}
        self.user_name_parts = {}
        
        # Preprocess user names
        for user_id, user_info in users_data.items():
            name = user_info.get('name', '') if user_info else ''
            if not isinstance(name, str):
                name = ''
                
            self.user_names[user_id] = name.strip()
            self.user_name_parts[user_id] = [
                part for part in self._normalize_text(name).split() 
                if part and len(part) > 1
            ]
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing accents, special chars, and standardizing case."""
        if not text or not isinstance(text, str):
            return ""
        
        # Convert to lowercase and normalize unicode characters
        text = text.lower()
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        
        # Remove special characters and normalize whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        return text
    
    def _extract_name_candidates(self, description: str) -> List[str]:
        """Extract potential name candidates from transaction description."""
        if not description:
            return []
        
        # Preprocessing and regex patterns combined for efficiency
        clean_desc = re.sub(r'([a-zA-Z])for\s+[Dd]eel', r'\1 for Deel', description.replace('  ', ' '))
        clean_desc = re.sub(r'(?<![A-Za-z]),', ' , ', clean_desc)
        clean_desc = re.sub(r',(?![A-Za-z\s])', ' , ', clean_desc)
        clean_desc = re.sub(r'ref\s+([A-Za-z0-9])', r'ref \1', clean_desc)
        clean_desc = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_desc)
        
        # Combined patterns for name extraction
        patterns = {
            'standard': r'[Ff]rom\s+([^,]+?)(?:\s+for\s+[Dd]eel|,\s*for\s+[Dd]eel|\s*for\s+[Dd]eel)',
            'transfer': r'(?:[Tt]ransfer|[Pp]ayment|[Rr]eceived|[Rr]equest)\s+from\s+([^,]+?)(?:\s+for\s+[Dd]eel|,|\s+ref)',
            'to_deel': r'[Tt]o\s+[Dd]eel,?\s+[Ff]rom\s+([^,]+?)(?:\s+for|,|ref)',
            'camelcase': r'[Ff]rom\s+([A-Z][a-z]+(?:[A-Z][a-z]+)+)(?:\s+for|\s*for)',
            'comma': r'[Ff]rom\s+([A-Za-z]+[\s,]+[A-Za-z]+)(?:\s+for|\s*,)',
            'reference': r'ref:\s+([^,]+?)(?:$|,)',
            'cc': r'[Cc][Cc]\s+([^,]+?)(?:$|,|ref)',
            'from_general': r'[Ff]rom\s+([^,]+?)(?:$|\s|,|ref)',
            'ref_code': r'ACC//[^/]*//CNTR(?:[^A-Za-z0-9]*([A-Za-z][A-Za-z\s]+))?',
            'ref_suffix': r'//CNTR[^A-Za-z0-9]*([A-Za-z][A-Za-z\s]+)'
        }
        
        candidates = set()
        
        # Extract candidates using all patterns
        for pattern in patterns.values():
            for text in [description, clean_desc]:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        for m in match:
                            if m and len(m.strip()) > 2:
                                candidates.add(m.strip())
                    elif match and len(match.strip()) > 2:
                        candidates.add(match.strip())
        
        # Process candidates more efficiently
        processed_candidates = []
        skip_terms = {'deel', 'for deel', 'ref', 'acc', 'from', 'to'}
        
        for candidate in candidates:
            candidate = candidate.strip()
            
            # Skip obvious non-names
            if candidate.lower() in skip_terms or 'ACC//' in candidate or \
               candidate.startswith('ref ') or bool(re.match(r'^[0-9]+$', candidate)):
                continue
            
            # Handle comma version
            if ',' in candidate:
                processed_candidates.append(candidate)
                candidate = candidate.replace(',', ' ')
            
            # Clean candidate
            candidate = re.sub(r'[|;\'"\\\[\]{}()]', ' ', candidate)
            candidate = re.sub(r'\s{2,}', ' ', candidate)
            candidate = candidate.strip()
            candidate = re.sub(r'^(?:ref|cc|from|to|debit)\s+', '', candidate, flags=re.IGNORECASE)
            candidate = re.sub(r'^[^\w\s]+', '', candidate)
            candidate = re.sub(r'\s+for\s+[Dd]eel$', '', candidate)
            candidate = re.sub(r'for\s+$', '', candidate, flags=re.IGNORECASE)
            
            if candidate and len(candidate) > 2:
                processed_candidates.append(candidate)
                
                # Handle run-together names
                if len(candidate) > 5 and ' ' not in candidate and not candidate.isupper():
                    processed_candidates.extend(self._generate_name_splits(candidate))
        
        return processed_candidates
    
    def _generate_name_splits(self, name: str) -> List[str]:
        """Generate potential splits for run-together names using patterns rather than hardcoded lists."""
        results = []
        
        # 1. Handle camelCase or PascalCase (this is language-neutral)
        if re.search(r'[a-z][A-Z]', name) or re.search(r'[A-Z][a-z]+[A-Z]', name):
            parts = re.findall(r'[A-Z][a-z]+', name)
            if len(parts) >= 2:
                results.append(' '.join(parts))
        
        # 2. Try N-gram based splitting for longer strings
        if len(name) > 8 and ' ' not in name:
            # Try splitting at different positions and check if both parts look name-like
            for i in range(3, len(name) - 3):
                # Check if splitting here makes sense (don't split inside a lowercase sequence)
                if name[i-1].islower() and name[i].islower():
                    continue
                    
                first_part = name[:i].strip()
                last_part = name[i:].strip()
                
                # Only add if both parts are reasonable length for name components
                if len(first_part) >= 2 and len(last_part) >= 3:
                    # Create variants with appropriate capitalization
                    results.append(f"{first_part} {last_part}")
                    results.append(f"{first_part.capitalize()} {last_part.capitalize()}")
        
        return results
    
    def _calculate_match_score(self, candidate: str, user_id: str) -> float:
        """Calculate match score between a candidate name and user."""
        user_name = self.user_names.get(user_id, "")
        if not user_name or not candidate:
            return 0
        
        # Create name variants
        candidate_variants = [candidate]
        user_variants = [user_name]
        
        # Add comma variations
        for text, variants in [(candidate, candidate_variants), (user_name, user_variants)]:
            if ',' in text:
                variants.append(text.replace(',', ' '))
                parts = [p.strip() for p in text.split(',')]
                if len(parts) == 2 and all(parts):
                    variants.append(f"{parts[1]} {parts[0]}")
                    
        # Split run-together names
        if len(candidate) > 6 and ' ' not in candidate:
            candidate_variants.extend(self._generate_name_splits(candidate))
        
        # Perfect match check
        for user_var in user_variants:
            for cand_var in candidate_variants:
                if self._normalize_text(cand_var) == self._normalize_text(user_var):
                    return 100
                    
        # Find best partial match
        best_score = 0
        for user_var in user_variants:
            for cand_var in candidate_variants:
                # Overall similarity (20%)
                norm_user = self._normalize_text(user_var)
                norm_candidate = self._normalize_text(cand_var)
                token_similarity = max(
                    fuzz.token_set_ratio(norm_candidate, norm_user) / 100,
                    fuzz.token_sort_ratio(norm_candidate, norm_user) / 100
                )
                overall_score = token_similarity * 22
                
                # Name part matching (58%)
                user_parts = self.user_name_parts.get(user_id, [])
                if not user_parts:
                    continue
                    
                # Calculate match details for name parts
                matches = {"first": 0, "middle": 0, "last": 0, "matched": 0, "total": len(user_parts)}
                candidate_parts = [p for p in self._normalize_text(cand_var).split() if p and len(p) > 1]
                
                if not candidate_parts:
                    continue
                
                # Check each user name part against candidate parts
                for i, user_part in enumerate(user_parts):
                    best_part_score = 0
                    for cand_part in candidate_parts:
                        if user_part == cand_part:
                            best_part_score = 100
                            break
                        best_part_score = max(best_part_score, fuzz.ratio(user_part, cand_part))
                    
                    if best_part_score >= 80:
                        matches["matched"] += 1
                    
                    # Assign to name positions
                    if i == 0:
                        matches["first"] = best_part_score
                    elif i == len(user_parts) - 1:
                        matches["last"] = best_part_score
                    else:
                        matches["middle"] = max(matches["middle"], best_part_score)
                
                # Calculate parts score with weights
                parts_score = (
                    (matches["first"] / 100) * 25 +  # First name (25%)
                    (matches["middle"] / 100) * 3 +  # Middle name (3%)
                    (matches["last"] / 100) * 30     # Last name (30%)
                )
                
                # Coverage score (20%)
                coverage_score = 0
                if matches["total"] > 0:
                    coverage = matches["matched"] / matches["total"]
                    if matches["total"] >= 3:
                        missing_parts = matches["total"] - matches["matched"]
                        if missing_parts > 0:
                            coverage *= (1 - 0.15 * missing_parts)
                    coverage_score = coverage * 20
                
                # Combine scores with adjustments
                score = overall_score + parts_score + coverage_score
                
                # Adjustments for partial/complete matches
                has_multiple_parts = matches["total"] > 1
                candidate_is_single_word = len(norm_candidate.split()) == 1
                
                if candidate_is_single_word and has_multiple_parts:
                    score *= 0.85
                
                all_parts_matched = matches["matched"] == matches["total"]
                if all_parts_matched and has_multiple_parts:
                    score *= 1.02
                    score = min(score, 95)
                
                best_score = max(best_score, score)
        
        return min(100, max(0, round(best_score, 1)))
    
    def find_matching_users(self, description: str, threshold: int = 55) -> List[Dict]:
        """
        Find users matching a transaction description.
        
        Args:
            description: Transaction description text
            threshold: Minimum match score (0-100)
            
        Returns:
            List of matching users with scores, sorted by relevance
        """
        if not description:
            return []
        
        # Extract name candidates from description
        candidates = self._extract_name_candidates(description)
        if not candidates:
            return []
        
        # Find best matches for each user
        matches = []
        for user_id, user_info in self.users_data.items():
            if not user_info or not user_info.get('name'):
                continue
            
            # Find best matching candidate for this user
            best_score = max(self._calculate_match_score(candidate, user_id) for candidate in candidates)
            
            # Add if score meets threshold
            if best_score >= threshold:
                matches.append({
                    'id': user_id,
                    'match_metric': best_score
                })
        
        # Sort by score (highest first)
        return sorted(matches, key=lambda x: x['match_metric'], reverse=True)
