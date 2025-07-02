"""
Statistical Analysis Utilities for Scientific AI Orchestrator
------------------------------------------------------------

Provides advanced statistical analysis, meta-analysis, and data interpretation
capabilities for scientific findings.
"""

import re
import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.models import NumericalFinding

@dataclass
class StatisticalSummary:
    """Summary of statistical findings across multiple studies."""
    total_studies: int
    studies_with_p_values: int
    significant_findings: int
    average_sample_size: float
    effect_size_summary: Dict[str, Any]
    confidence_interval_summary: Dict[str, Any]
    statistical_power_estimate: float
    publication_bias_risk: str
    heterogeneity_score: float

class StatisticalAnalyzer:
    """Advanced statistical analysis for scientific findings."""
    
    def __init__(self):
        # Effect size interpretation thresholds (Cohen's d)
        self.effect_size_thresholds = {
            'small': 0.2,
            'medium': 0.5,
            'large': 0.8
        }
    
    def analyze_findings(self, findings: List[NumericalFinding]) -> StatisticalSummary:
        """Perform comprehensive statistical analysis on findings."""
        if not findings:
            return self._empty_summary()
        
        # Extract and analyze different types of data
        p_values = self._extract_p_values(findings)
        effect_sizes = self._extract_effect_sizes(findings)
        sample_sizes = self._extract_sample_sizes(findings)
        confidence_intervals = self._extract_confidence_intervals(findings)
        
        # Calculate summary statistics
        total_studies = len(findings)
        studies_with_p_values = len([f for f in findings if f.p_values])
        significant_findings = self._count_significant_findings(p_values)
        average_sample_size = statistics.mean(sample_sizes) if sample_sizes else 0
        
        # Analyze effect sizes
        effect_size_summary = self._analyze_effect_sizes(effect_sizes)
        
        # Analyze confidence intervals
        confidence_interval_summary = self._analyze_confidence_intervals(confidence_intervals)
        
        # Estimate statistical power
        statistical_power = self._estimate_statistical_power(sample_sizes, p_values)
        
        # Assess publication bias risk
        publication_bias_risk = self._assess_publication_bias(p_values, effect_sizes)
        
        # Calculate heterogeneity
        heterogeneity_score = self._calculate_heterogeneity(effect_sizes)
        
        return StatisticalSummary(
            total_studies=total_studies,
            studies_with_p_values=studies_with_p_values,
            significant_findings=significant_findings,
            average_sample_size=average_sample_size,
            effect_size_summary=effect_size_summary,
            confidence_interval_summary=confidence_interval_summary,
            statistical_power_estimate=statistical_power,
            publication_bias_risk=publication_bias_risk,
            heterogeneity_score=heterogeneity_score
        )
    
    def _extract_p_values(self, findings: List[NumericalFinding]) -> List[float]:
        """Extract and parse p-values from findings."""
        p_values = []
        for finding in findings:
            for p_val_str in finding.p_values:
                try:
                    p_val = self._parse_p_value(p_val_str)
                    if p_val is not None:
                        p_values.append(p_val)
                except (ValueError, TypeError):
                    continue
        return p_values
    
    def _extract_effect_sizes(self, findings: List[NumericalFinding]) -> List[float]:
        """Extract and parse effect sizes from findings."""
        effect_sizes = []
        for finding in findings:
            for effect_str in finding.effect_sizes:
                try:
                    effect_size = self._parse_effect_size(effect_str)
                    if effect_size is not None:
                        effect_sizes.append(effect_size)
                except (ValueError, TypeError):
                    continue
        return effect_sizes
    
    def _extract_sample_sizes(self, findings: List[NumericalFinding]) -> List[int]:
        """Extract sample sizes from findings."""
        sample_sizes = []
        for finding in findings:
            for sample_str in finding.sample_sizes:
                try:
                    sample_size = self._parse_sample_size(sample_str)
                    if sample_size is not None:
                        sample_sizes.append(sample_size)
                except (ValueError, TypeError):
                    continue
        return sample_sizes
    
    def _extract_confidence_intervals(self, findings: List[NumericalFinding]) -> List[Tuple[float, float]]:
        """Extract confidence intervals from findings."""
        intervals = []
        for finding in findings:
            for ci_str in finding.confidence_intervals:
                try:
                    interval = self._parse_confidence_interval(ci_str)
                    if interval is not None:
                        intervals.append(interval)
                except (ValueError, TypeError):
                    continue
        return intervals
    
    def _parse_p_value(self, p_val_str: str) -> Optional[float]:
        """Parse p-value from string."""
        p_val_str = p_val_str.lower().replace('p', '').replace('=', '').replace('<', '').replace('>', '').strip()
        if 'e-' in p_val_str:
            return float(p_val_str)
        try:
            return float(p_val_str)
        except ValueError:
            return None
    
    def _parse_effect_size(self, effect_str: str) -> Optional[float]:
        """Parse effect size from string."""
        numbers = re.findall(r'[-+]?\d*\.?\d+', effect_str)
        if numbers:
            return float(numbers[0])
        return None
    
    def _parse_sample_size(self, sample_str: str) -> Optional[int]:
        """Parse sample size from string."""
        numbers = re.findall(r'\d+', sample_str)
        if numbers:
            return int(numbers[0])
        return None
    
    def _parse_confidence_interval(self, ci_str: str) -> Optional[Tuple[float, float]]:
        """Parse confidence interval from string."""
        numbers = re.findall(r'[-+]?\d*\.?\d+', ci_str)
        if len(numbers) >= 2:
            return (float(numbers[0]), float(numbers[1]))
        return None
    
    def _count_significant_findings(self, p_values: List[float]) -> int:
        """Count significant findings (p < 0.05)."""
        return sum(1 for p in p_values if p < 0.05)
    
    def _analyze_effect_sizes(self, effect_sizes: List[float]) -> Dict[str, Any]:
        """Analyze effect sizes and provide interpretation."""
        if not effect_sizes:
            return {"message": "No effect sizes found"}
        
        mean_effect = statistics.mean(effect_sizes)
        std_effect = statistics.stdev(effect_sizes) if len(effect_sizes) > 1 else 0
        
        magnitude = "small"
        if abs(mean_effect) >= self.effect_size_thresholds['large']:
            magnitude = "large"
        elif abs(mean_effect) >= self.effect_size_thresholds['medium']:
            magnitude = "medium"
        
        interpretation = f"The average effect size is {magnitude} (d = {mean_effect:.3f})"
        
        return {
            "count": len(effect_sizes),
            "mean": mean_effect,
            "std": std_effect,
            "magnitude": magnitude,
            "interpretation": interpretation,
            "range": (min(effect_sizes), max(effect_sizes))
        }
    
    def _analyze_confidence_intervals(self, intervals: List[Tuple[float, float]]) -> Dict[str, Any]:
        """Analyze confidence intervals."""
        if not intervals:
            return {"message": "No confidence intervals found"}
        
        coverage_zero = sum(1 for low, high in intervals if low <= 0 <= high)
        coverage_percentage = (coverage_zero / len(intervals)) * 100
        
        widths = [high - low for low, high in intervals]
        avg_width = statistics.mean(widths)
        
        return {
            "count": len(intervals),
            "coverage_zero_percentage": coverage_percentage,
            "average_width": avg_width,
            "interpretation": f"{coverage_percentage:.1f}% of intervals include zero"
        }
    
    def _estimate_statistical_power(self, sample_sizes: List[int], p_values: List[float]) -> float:
        """Estimate statistical power based on sample sizes and effect sizes."""
        if not sample_sizes or not p_values:
            return 0.0
        
        avg_sample_size = statistics.mean(sample_sizes)
        
        if avg_sample_size >= 100:
            return 0.9
        elif avg_sample_size >= 50:
            return 0.8
        elif avg_sample_size >= 30:
            return 0.7
        else:
            return 0.5
    
    def _assess_publication_bias(self, p_values: List[float], effect_sizes: List[float]) -> str:
        """Assess risk of publication bias."""
        if not p_values:
            return "insufficient_data"
        
        significant = sum(1 for p in p_values if p < 0.05)
        total = len(p_values)
        significant_ratio = significant / total if total > 0 else 0
        
        if significant_ratio > 0.8:
            return "high_risk"
        elif significant_ratio > 0.6:
            return "moderate_risk"
        else:
            return "low_risk"
    
    def _calculate_heterogeneity(self, effect_sizes: List[float]) -> float:
        """Calculate heterogeneity score (I² equivalent)."""
        if len(effect_sizes) < 2:
            return 0.0
        
        mean_effect = statistics.mean(effect_sizes)
        std_effect = statistics.stdev(effect_sizes)
        
        if mean_effect == 0:
            return 0.0
        
        cv = abs(std_effect / mean_effect)
        return min(1.0, cv / 2.0)
    
    def _empty_summary(self) -> StatisticalSummary:
        """Return empty summary when no findings are available."""
        return StatisticalSummary(
            total_studies=0,
            studies_with_p_values=0,
            significant_findings=0,
            average_sample_size=0.0,
            effect_size_summary={"message": "No data"},
            confidence_interval_summary={"message": "No data"},
            statistical_power_estimate=0.0,
            publication_bias_risk="insufficient_data",
            heterogeneity_score=0.0
        )
    
    def generate_meta_analysis_report(self, findings: List[NumericalFinding]) -> str:
        """Generate a comprehensive meta-analysis report."""
        summary = self.analyze_findings(findings)
        
        report = f"""
# Meta-Analysis Report

## Study Overview
- **Total Studies**: {summary.total_studies}
- **Studies with P-values**: {summary.studies_with_p_values}
- **Significant Findings**: {summary.significant_findings}
- **Average Sample Size**: {summary.average_sample_size:.0f}

## Effect Size Analysis
{summary.effect_size_summary.get('interpretation', 'No effect size data available')}

## Statistical Power
- **Estimated Power**: {summary.statistical_power_estimate:.1%}
- **Assessment**: {'Adequate' if summary.statistical_power_estimate >= 0.8 else 'Inadequate'}

## Publication Bias Risk
- **Risk Level**: {summary.publication_bias_risk.replace('_', ' ').title()}

## Heterogeneity
- **Heterogeneity Score**: {summary.heterogeneity_score:.3f}
- **Assessment**: {'High' if summary.heterogeneity_score > 0.5 else 'Low'} heterogeneity

## Confidence Intervals
{summary.confidence_interval_summary.get('interpretation', 'No confidence interval data available')}
"""
        return report.strip()