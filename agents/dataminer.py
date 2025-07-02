"""
DataMiner – numerical data extraction agent
-------------------------------------------

Extracts numerical findings from scientific abstracts and papers using
advanced LLM techniques and sophisticated regex fallback patterns.
"""

from openai import OpenAI
import os
import re
import json
from typing import List, Dict, Any, Optional
from app.models import EvidenceItem, NumericalFinding
from utils.retry import retry_with_backoff, safe_execute

class DataMiner:
    """Extracts numerical findings from an EvidenceItem using LLM and regex fallback."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Enhanced regex patterns for different types of numerical data
        self.patterns = {
            'percentages': [
                r'\b\d{1,3}(?:\.\d+)?\s*%',  # 95%, 95.5%
                r'\b\d{1,3}(?:\.\d+)?\s*percent',  # 95 percent
                r'\b\d{1,3}(?:\.\d+)?\s*per\s*cent',  # 95 per cent
            ],
            'p_values': [
                r'p\s*[<=>]\s*0?\.\d+',  # p < 0.05, p=0.001
                r'p\s*[<=>]\s*0?\.\d+e-\d+',  # p < 0.001e-3
                r'significant.*?p\s*[<=>]\s*0?\.\d+',  # significant p < 0.05
            ],
            'confidence_intervals': [
                r'CI\s*=\s*\[?\d+\.?\d*\s*[-–]\s*\d+\.?\d*\]?',  # CI = [1.2-3.4]
                r'confidence\s*interval.*?\d+\.?\d*\s*[-–]\s*\d+\.?\d*',  # confidence interval 1.2-3.4
                r'\(\d+\.?\d*,\s*\d+\.?\d*\)',  # (1.2, 3.4)
            ],
            'sample_sizes': [
                r'n\s*=\s*\d+',  # n = 100
                r'sample\s*size.*?\d+',  # sample size 100
                r'participants.*?\d+',  # participants 100
                r'subjects.*?\d+',  # subjects 100
            ],
            'effect_sizes': [
                r'Cohen\'s\s*d\s*=\s*[-+]?\d*\.?\d+',  # Cohen's d = 0.5
                r'effect\s*size.*?[-+]?\d*\.?\d+',  # effect size 0.5
                r'odds\s*ratio.*?[-+]?\d*\.?\d+',  # odds ratio 1.5
                r'risk\s*ratio.*?[-+]?\d*\.?\d+',  # risk ratio 1.5
            ],
            'statistical_tests': [
                r't\s*\(\s*\d+\s*\)\s*=\s*[-+]?\d*\.?\d+',  # t(50) = 2.5
                r'F\s*\(\s*\d+,\s*\d+\s*\)\s*=\s*[-+]?\d*\.?\d+',  # F(2,50) = 3.5
                r'chi-square.*?[-+]?\d*\.?\d+',  # chi-square 5.2
                r'ANOVA.*?[-+]?\d*\.?\d+',  # ANOVA 3.5
            ]
        }

    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def run(self, evidence: EvidenceItem) -> NumericalFinding:
        """
        Extract numerical findings using LLM with enhanced fallback.
        
        Parameters
        ----------
        evidence : EvidenceItem
            The evidence item containing the text to analyze
            
        Returns
        -------
        NumericalFinding
            Extracted numerical data
        """
        # Try LLM extraction first
        llm_result = self._llm_extract(evidence.summary)
        if llm_result and self._validate_extraction(llm_result):
            return llm_result
        
        # Fallback to enhanced regex
        print(f"[DataMiner] LLM extraction failed or invalid, using regex fallback")
        return self._regex_extract(evidence.summary)

    def _llm_extract(self, text: str) -> Optional[NumericalFinding]:
        """Extract numerical data using LLM."""
        prompt = (
            "Extract all numerical findings from the following scientific text. "
            "Focus on percentages, p-values, confidence intervals, sample sizes, "
            "effect sizes, and statistical test results. "
            "Return ONLY valid JSON in this exact format:\n"
            "{\n"
            '  "percentages": ["95%", "significant at 5%"],\n'
            '  "p_values": ["p < 0.05", "p = 0.001"],\n'
            '  "confidence_intervals": ["CI = [1.2-3.4]", "(0.5, 2.1)"],\n'
            '  "sample_sizes": ["n = 100", "sample size 50"],\n'
            '  "effect_sizes": ["Cohen\'s d = 0.5", "odds ratio 1.5"],\n'
            '  "statistical_tests": ["t(50) = 2.5", "F(2,50) = 3.5"]\n'
            "}\n"
            f"\nTEXT TO ANALYZE:\n{text}"
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            data = response.choices[0].message.content
            parsed = json.loads(data)
            
            # Ensure all required fields are present
            for field in ['percentages', 'p_values', 'confidence_intervals', 'sample_sizes']:
                if field not in parsed:
                    parsed[field] = []
            
            # Add new fields if not present
            if 'effect_sizes' not in parsed:
                parsed['effect_sizes'] = []
            if 'statistical_tests' not in parsed:
                parsed['statistical_tests'] = []
            
            return NumericalFinding(**parsed)
            
        except Exception as exc:
            print(f"[DataMiner] LLM extraction error: {exc}")
            return None

    def _regex_extract(self, text: str) -> NumericalFinding:
        """Enhanced regex extraction with multiple patterns."""
        findings = {}
        
        for category, patterns in self.patterns.items():
            findings[category] = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                findings[category].extend(matches)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_matches = []
            for match in findings[category]:
                if match.lower() not in seen:
                    seen.add(match.lower())
                    unique_matches.append(match)
            findings[category] = unique_matches
        
        # Map to NumericalFinding fields
        return NumericalFinding(
            percentages=findings.get('percentages', []),
            p_values=findings.get('p_values', []),
            confidence_intervals=findings.get('confidence_intervals', []),
            sample_sizes=findings.get('sample_sizes', []),
            effect_sizes=findings.get('effect_sizes', []),
            statistical_tests=findings.get('statistical_tests', [])
        )

    def _validate_extraction(self, finding: NumericalFinding) -> bool:
        """Validate that the extraction contains meaningful data."""
        total_findings = (
            len(finding.percentages) + 
            len(finding.p_values) + 
            len(finding.confidence_intervals) + 
            len(finding.sample_sizes)
        )
        
        # Check if we have at least some numerical data
        if total_findings == 0:
            return False
        
        # Check for reasonable values (basic sanity checks)
        for percentage in finding.percentages:
            try:
                value = float(percentage.replace('%', '').strip())
                if value < 0 or value > 1000:  # Allow for percentages > 100% in some cases
                    return False
            except ValueError:
                continue
        
        return True

    def extract_from_batch(self, evidence_items: List[EvidenceItem]) -> List[NumericalFinding]:
        """
        Extract numerical findings from multiple evidence items.
        
        Parameters
        ----------
        evidence_items : List[EvidenceItem]
            List of evidence items to process
            
        Returns
        -------
        List[NumericalFinding]
            List of extracted numerical findings
        """
        findings = []
        for i, evidence in enumerate(evidence_items):
            print(f"[DataMiner] Processing evidence {i+1}/{len(evidence_items)}")
            finding = safe_execute(self.run, evidence, default_return=NumericalFinding())
            findings.append(finding)
        return findings

    def get_statistical_summary(self, findings: List[NumericalFinding]) -> Dict[str, Any]:
        """
        Generate a statistical summary from multiple findings.
        
        Parameters
        ----------
        findings : List[NumericalFinding]
            List of numerical findings
            
        Returns
        -------
        Dict[str, Any]
            Statistical summary
        """
        summary = {
            'total_papers': len(findings),
            'papers_with_p_values': 0,
            'papers_with_effect_sizes': 0,
            'significant_findings': 0,
            'average_sample_size': 0,
            'common_effect_sizes': [],
            'statistical_tests_used': []
        }
        
        sample_sizes = []
        effect_sizes = []
        all_tests = set()
        
        for finding in findings:
            if finding.p_values:
                summary['papers_with_p_values'] += 1
                # Count significant findings (p < 0.05)
                for p_val in finding.p_values:
                    try:
                        if 'p < 0.05' in p_val or 'p<0.05' in p_val:
                            summary['significant_findings'] += 1
                            break
                    except:
                        continue
            
            if finding.effect_sizes:
                summary['papers_with_effect_sizes'] += 1
                effect_sizes.extend(finding.effect_sizes)
            
            # Extract sample sizes
            for sample in finding.sample_sizes:
                try:
                    size = int(re.findall(r'\d+', sample)[0])
                    sample_sizes.append(size)
                except:
                    continue
            
            # Collect statistical tests
            all_tests.update(finding.statistical_tests)
        
        if sample_sizes:
            summary['average_sample_size'] = sum(sample_sizes) / len(sample_sizes)
        
        summary['common_effect_sizes'] = effect_sizes[:5]  # Top 5
        summary['statistical_tests_used'] = list(all_tests)
        
        return summary 