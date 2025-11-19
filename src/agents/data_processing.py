"""Data Processing Agent for AI Study Coach.

Handles all data processing tasks including:
- Cleaning and validating user data
- Analyzing study patterns and performance metrics
- Aggregating data from multiple sources
- Generating insights and statistics
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class DataProcessingAgent:
    """Manages data processing and analytics for the study coach system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processed_data = defaultdict(list)
        self.statistics = {}
        
    def clean_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate input data."""
        try:
            cleaned_data = {}
            for key, value in raw_data.items():
                # Remove null values
                if value is not None:
                    # Strip whitespace from strings
                    if isinstance(value, str):
                        cleaned_data[key] = value.strip()
                    else:
                        cleaned_data[key] = value
            
            self.logger.info(f"Cleaned data with {len(cleaned_data)} fields")
            return cleaned_data
        except Exception as e:
            self.logger.error(f"Error cleaning data: {str(e)}")
            return {}
    
    def validate_data(self, data: Dict[str, Any], schema: Dict[str, type]) -> bool:
        """Validate data against schema."""
        try:
            for field, expected_type in schema.items():
                if field in data:
                    if not isinstance(data[field], expected_type):
                        self.logger.warning(f"Field {field} type mismatch")
                        return False
            return True
        except Exception as e:
            self.logger.error(f"Error validating data: {str(e)}")
            return False
    
    def analyze_study_patterns(self, study_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze study patterns and generate insights."""
        try:
            if not study_sessions:
                return {'error': 'No study sessions to analyze'}
            
            # Calculate metrics
            total_time = sum(s.get('duration', 0) for s in study_sessions)
            avg_session_length = total_time / len(study_sessions) if study_sessions else 0
            
            # Analyze subjects
            subjects = defaultdict(int)
            for session in study_sessions:
                subject = session.get('subject', 'unknown')
                subjects[subject] += session.get('duration', 0)
            
            # Find most studied subject
            most_studied = max(subjects.items(), key=lambda x: x[1]) if subjects else ('none', 0)
            
            analysis = {
                'total_sessions': len(study_sessions),
                'total_time_minutes': total_time,
                'average_session_length': avg_session_length,
                'subjects_studied': dict(subjects),
                'most_studied_subject': most_studied[0],
                'most_studied_time': most_studied[1]
            }
            
            self.logger.info(f"Analyzed {len(study_sessions)} study sessions")
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {str(e)}")
            return {'error': str(e)}
    
    def calculate_performance_metrics(self, quiz_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics from quiz results."""
        try:
            if not quiz_results:
                return {'error': 'No quiz results to analyze'}
            
            total_score = sum(q.get('score', 0) for q in quiz_results)
            avg_score = total_score / len(quiz_results) if quiz_results else 0
            
            # Track performance by subject
            subject_performance = defaultdict(list)
            for quiz in quiz_results:
                subject = quiz.get('subject', 'unknown')
                score = quiz.get('score', 0)
                subject_performance[subject].append(score)
            
            # Calculate subject averages
            subject_avg = {}
            for subject, scores in subject_performance.items():
                subject_avg[subject] = sum(scores) / len(scores) if scores else 0
            
            metrics = {
                'total_quizzes': len(quiz_results),
                'average_score': avg_score,
                'subject_performance': subject_avg,
                'highest_score': max((q.get('score', 0) for q in quiz_results), default=0),
                'lowest_score': min((q.get('score', 0) for q in quiz_results), default=0)
            }
            
            self.logger.info(f"Calculated metrics for {len(quiz_results)} quizzes")
            return metrics
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")
            return {'error': str(e)}
    
    def aggregate_data(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate data from multiple sources."""
        try:
            aggregated = defaultdict(list)
            for source in data_sources:
                source_type = source.get('type', 'unknown')
                aggregated[source_type].append(source.get('data', {}))
            
            self.logger.info(f"Aggregated data from {len(data_sources)} sources")
            return dict(aggregated)
        except Exception as e:
            self.logger.error(f"Error aggregating data: {str(e)}")
            return {}
    
    def generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from analysis."""
        insights = []
        try:
            # Study pattern insights
            if 'average_session_length' in analysis:
                avg_length = analysis['average_session_length']
                if avg_length < 25:
                    insights.append("Consider longer study sessions for better retention.")
                elif avg_length > 90:
                    insights.append("Take breaks to avoid fatigue during long sessions.")
            
            # Performance insights
            if 'average_score' in analysis:
                avg_score = analysis['average_score']
                if avg_score < 60:
                    insights.append("Focus on foundational concepts to improve scores.")
                elif avg_score > 85:
                    insights.append("Great performance! Consider advanced topics.")
            
            # Subject-specific insights
            if 'subject_performance' in analysis:
                subject_perf = analysis['subject_performance']
                weak_subjects = [s for s, score in subject_perf.items() if score < 65]
                if weak_subjects:
                    insights.append(f"Need improvement in: {', '.join(weak_subjects)}")
            
            self.logger.info(f"Generated {len(insights)} insights")
            return insights
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return ["Unable to generate insights at this time."]
    
    def export_data(self, data: Dict[str, Any], format_type: str = 'json') -> str:
        """Export data in specified format."""
        try:
            if format_type == 'json':
                return json.dumps(data, indent=2)
            else:
                self.logger.warning(f"Unsupported format: {format_type}")
                return str(data)
        except Exception as e:
            self.logger.error(f"Error exporting data: {str(e)}")
            return ""
    
    def calculate_trends(self, time_series_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trends from time series data."""
        try:
            if len(time_series_data) < 2:
                return {'error': 'Insufficient data for trend analysis'}
            
            # Sort by timestamp
            sorted_data = sorted(time_series_data, key=lambda x: x.get('timestamp', ''))
            
            # Calculate simple trends
            first_value = sorted_data[0].get('value', 0)
            last_value = sorted_data[-1].get('value', 0)
            
            change = last_value - first_value
            percent_change = (change / first_value * 100) if first_value != 0 else 0
            
            trend = {
                'direction': 'increasing' if change > 0 else 'decreasing' if change < 0 else 'stable',
                'absolute_change': change,
                'percent_change': round(percent_change, 2),
                'data_points': len(sorted_data)
            }
            
            self.logger.info(f"Calculated trends from {len(sorted_data)} data points")
            return trend
        except Exception as e:
            self.logger.error(f"Error calculating trends: {str(e)}")
            return {'error': str(e)}
