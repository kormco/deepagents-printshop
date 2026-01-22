"""
QA Orchestrator Agent

Master orchestration agent that coordinates all specialized QA agents in an automated pipeline
with quality gates, decision logic, and iterative improvement workflows.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.qa_orchestrator.quality_gates import QualityGateManager, QualityThresholds
from agents.qa_orchestrator.workflow_coordinator import WorkflowCoordinator, WorkflowExecution
from tools.version_manager import VersionManager


class QAOrchestratorAgent:
    """
    QA Orchestrator Agent - The master coordinator for multi-agent quality assurance.

    Features:
    - Multi-agent workflow orchestration
    - Quality gate enforcement
    - Iterative improvement cycles
    - Intelligent escalation logic
    - Comprehensive reporting
    """

    def __init__(self, memory_dir: str = ".deepagents/qa_orchestrator/memories",
                 content_source: str = "research_report"):
        """
        Initialize the QA orchestrator agent.

        Args:
            memory_dir: Directory for storing agent memories
            content_source: Content source folder (e.g., 'research_report', 'magazine')
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.content_source = content_source

        # Initialize components
        self.workflow_coordinator = WorkflowCoordinator(content_source=content_source)
        self.quality_gate_manager = QualityGateManager()
        self.version_manager = VersionManager()

        # Paths
        self.reports_dir = Path("artifacts/agent_reports/orchestration")
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize memory
        self.init_memory()

    def init_memory(self):
        """Initialize agent memory files."""
        memory_files = {
            "quality_thresholds.md": """# Quality Thresholds and Gates

## Content Quality Standards
- **Minimum Acceptable**: 80/100 (good baseline quality)
- **Good Quality**: 85/100 (professional standard)
- **Excellent Quality**: 90/100 (publication ready)

## LaTeX Quality Standards
- **Minimum Acceptable**: 85/100 (professional formatting)
- **Good Quality**: 90/100 (high-quality typography)
- **Excellent Quality**: 95/100 (publication perfect)

## Component Thresholds (out of 25 each)
- **Structure Minimum**: 22/25 (well-organized document)
- **Typography Minimum**: 20/25 (professional appearance)
- **Tables/Figures Minimum**: 20/25 (clear presentation)
- **Best Practices Minimum**: 20/25 (standards compliance)

## Workflow Control
- **Overall Target**: 85/100 (combined quality threshold)
- **Human Handoff**: 90/100 (ready for human review)
- **Maximum Iterations**: 3 cycles before escalation
- **Convergence Threshold**: <2 points improvement = plateau

## Escalation Rules
- Quality plateau reached after maximum iterations
- Persistent agent failures
- Quality regression detected
- Time limits exceeded
""",
            "workflow_patterns.md": """# Successful Workflow Patterns

## Standard Success Pattern
1. **Content Review**: v0 → v1_content_edited (target: 80+)
2. **LaTeX Optimization**: v1 → v2_latex_optimized (target: 85+)
3. **Quality Assessment**: Overall score 85+ → Human handoff

## Iteration Patterns
### Content Quality Issues
- Run additional content editor cycles
- Focus on grammar, readability, structure
- Target: Consistent 5+ point improvements

### LaTeX Quality Issues
- Re-run LaTeX specialist with higher optimization
- Address structure, typography, formatting
- Target: Professional formatting standards

### Combined Quality Issues
- Full pipeline iteration
- Coordinate improvements across agents
- Balance content quality vs. formatting quality

## Escalation Patterns
### Plateau Detection
- <2 points improvement over 2 iterations
- Quality good enough (85+) but not excellent
- → Human review recommended

### Persistent Failures
- Agent failures after retry attempts
- Quality regression between iterations
- → Human intervention required

### Time/Resource Limits
- Maximum iterations reached (3 cycles)
- Processing time exceeds limits
- → Escalate with current best quality
""",
            "escalation_rules.md": """# Human Escalation Decision Rules

## Automatic Escalation Triggers
1. **Quality Achievement**: Score ≥90 → Immediate handoff
2. **Target Achievement**: Score ≥85 at iteration limit → Handoff
3. **Plateau Detection**: <2 point improvement → Review needed
4. **Agent Failures**: Persistent processing failures → Intervention

## Escalation Types
### Success Escalation (Quality Achieved)
- Quality meets or exceeds targets
- Ready for human review and approval
- Low priority for human reviewer

### Plateau Escalation (Good but Stuck)
- Quality acceptable but not improving
- May benefit from human insight
- Medium priority for human reviewer

### Failure Escalation (Issues Detected)
- Persistent quality issues
- Agent processing failures
- Technical problems detected
- High priority for human intervention

## Escalation Information Package
- Complete quality progression report
- Version history and change tracking
- Agent performance analysis
- Specific issues and recommendations
- Estimated time for human review
""",
            "pipeline_optimization.md": """# Pipeline Optimization Strategies

## Agent Sequencing
- **Content First**: Always start with content quality
- **LaTeX Second**: Build on solid content foundation
- **Quality Gates**: Enforce thresholds at each step

## Iteration Strategies
### Focused Iteration
- Target specific agent when below threshold
- More efficient than full pipeline re-run
- Good for isolated quality issues

### Full Pipeline Iteration
- Re-run complete workflow
- Better for systematic quality issues
- Necessary when agents are interdependent

### Adaptive Thresholds
- Lower thresholds for difficult content
- Higher thresholds for simple content
- Context-aware quality expectations

## Performance Optimization
- **Version Reuse**: Skip processing if good version exists
- **Incremental Processing**: Only process changed content
- **Parallel Execution**: Run independent analyses simultaneously
- **Resource Management**: Balance quality vs. processing time

## Quality vs. Efficiency Trade-offs
- **Fast Track**: Single iteration for time-sensitive content
- **Standard Track**: 2-3 iterations for normal content
- **Premium Track**: Unlimited iterations for critical content
"""
        }

        for filename, content in memory_files.items():
            file_path = self.memory_dir / filename
            if not file_path.exists():
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def orchestrate_qa_pipeline(self,
                               starting_version: str = "v0_original",
                               workflow_id: Optional[str] = None,
                               quality_thresholds: Optional[QualityThresholds] = None) -> Dict:
        """
        Orchestrate complete QA pipeline from start to finish.

        Args:
            starting_version: Version to start the pipeline from
            workflow_id: Unique identifier for this workflow (auto-generated if None)
            quality_thresholds: Custom quality thresholds (uses defaults if None)

        Returns:
            Complete pipeline execution results
        """
        # Generate workflow ID if not provided
        if workflow_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            workflow_id = f"qa_pipeline_{timestamp}"

        print(f"🎯 QA ORCHESTRATOR: Starting Pipeline {workflow_id}")
        print("=" * 70)

        # Update quality thresholds if provided
        if quality_thresholds:
            self.quality_gate_manager.thresholds = quality_thresholds

        # Execute complete workflow
        workflow_execution = self.workflow_coordinator.run_complete_workflow(
            workflow_id=workflow_id,
            starting_version=starting_version
        )

        # Generate comprehensive results
        results = self.compile_pipeline_results(workflow_execution)

        # Save pipeline report
        self.save_pipeline_report(results, workflow_id)

        print("=" * 70)
        print(f"🎯 QA ORCHESTRATOR: Pipeline {workflow_id} Complete")
        self.print_pipeline_summary(results)

        return results

    def compile_pipeline_results(self, workflow: WorkflowExecution) -> Dict:
        """
        Compile comprehensive pipeline results.

        Args:
            workflow: Completed workflow execution

        Returns:
            Complete pipeline results dictionary
        """
        # Get workflow summary
        workflow_summary = self.workflow_coordinator.get_workflow_summary(workflow)

        # Get final quality assessment
        final_assessment = workflow.quality_assessments[-1] if workflow.quality_assessments else None

        # Analyze version progression
        version_stats = self.version_manager.get_version_stats()

        # Compile comprehensive results
        results = {
            "pipeline_metadata": {
                "workflow_id": workflow.workflow_id,
                "execution_timestamp": workflow.start_time,
                "orchestrator_version": "1.0",
                "pipeline_duration": workflow.total_processing_time
            },
            "workflow_execution": workflow_summary,
            "quality_results": {
                "final_assessment": final_assessment.__dict__ if final_assessment else None,
                "quality_progression": [qa.__dict__ for qa in workflow.quality_assessments],
                "gate_evaluations": [qe.__dict__ for qe in workflow.quality_evaluations],
                "quality_thresholds": self.quality_gate_manager.thresholds.__dict__
            },
            "version_management": {
                "starting_version": workflow.agents_executed[0].version_created if workflow.agents_executed else None,
                "final_version": workflow.final_version,
                "versions_created": [r.version_created for r in workflow.agents_executed if r.success],
                "version_lineage": self.version_manager.get_version_lineage(workflow.final_version) if workflow.final_version else [],
                "repository_stats": version_stats
            },
            "agent_performance": {
                "agents_executed": len(workflow.agents_executed),
                "successful_executions": len([r for r in workflow.agents_executed if r.success]),
                "total_processing_time": sum(r.processing_time for r in workflow.agents_executed),
                "average_processing_time": sum(r.processing_time for r in workflow.agents_executed) / len(workflow.agents_executed) if workflow.agents_executed else 0,
                "agent_details": [r.__dict__ for r in workflow.agents_executed]
            },
            "pipeline_outcome": {
                "success": workflow.success,
                "human_handoff": workflow.human_handoff,
                "escalated": workflow.escalated,
                "iterations_completed": workflow.iterations_completed,
                "final_stage": workflow.current_stage.value,
                "ready_for_review": workflow.human_handoff or workflow.escalated
            }
        }

        return results

    def save_pipeline_report(self, results: Dict, workflow_id: str):
        """Save comprehensive pipeline report."""
        # JSON report
        json_path = self.reports_dir / f"{workflow_id}_pipeline_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        # Markdown report
        md_path = self.reports_dir / f"{workflow_id}_pipeline_summary.md"
        self.create_pipeline_markdown(results, md_path)

    def create_pipeline_markdown(self, results: Dict, output_path: Path):
        """Create human-readable pipeline summary."""
        metadata = results["pipeline_metadata"]
        workflow = results["workflow_execution"]
        quality = results["quality_results"]
        outcome = results["pipeline_outcome"]

        content = f"""# QA Pipeline Report: {metadata["workflow_id"]}

**Generated:** {metadata["execution_timestamp"]}
**Pipeline Duration:** {metadata["pipeline_duration"]:.2f} seconds
**Orchestrator Version:** {metadata["orchestrator_version"]}

## Pipeline Outcome

| Metric | Result |
|--------|--------|
| **Success** | {'✅ Yes' if outcome['success'] else '❌ No'} |
| **Human Handoff** | {'✅ Ready' if outcome['human_handoff'] else '⚠️ Not Ready'} |
| **Escalated** | {'⚠️ Yes' if outcome['escalated'] else '✅ No'} |
| **Iterations** | {outcome['iterations_completed']} |
| **Final Stage** | {outcome['final_stage']} |

## Quality Results

"""

        final_assessment = quality["final_assessment"]
        if final_assessment:
            content += f"""### Final Quality Assessment
- **Overall Score:** {final_assessment.get('overall_score', 'N/A')}/100
- **Content Score:** {final_assessment.get('content_score', 'N/A')}/100
- **LaTeX Score:** {final_assessment.get('latex_score', 'N/A')}/100

### LaTeX Component Scores
- **Structure:** {final_assessment.get('latex_structure', 'N/A')}/25
- **Typography:** {final_assessment.get('latex_typography', 'N/A')}/25
- **Tables/Figures:** {final_assessment.get('latex_tables_figures', 'N/A')}/25
- **Best Practices:** {final_assessment.get('latex_best_practices', 'N/A')}/25

"""

        # Quality progression
        quality_progression = quality["quality_progression"]
        if quality_progression:
            content += f"""### Quality Progression
| Iteration | Content Score | LaTeX Score | Overall Score |
|-----------|---------------|-------------|---------------|
"""
            for i, assessment in enumerate(quality_progression, 1):
                content_score = assessment.get('content_score', 'N/A')
                latex_score = assessment.get('latex_score', 'N/A')
                overall_score = assessment.get('overall_score', 'N/A')
                content += f"| {i} | {content_score} | {latex_score} | {overall_score} |\n"

        content += f"""
## Version Management

### Version Progression
- **Starting Version:** {results["version_management"]["starting_version"]}
- **Final Version:** {results["version_management"]["final_version"]}
- **Versions Created:** {len(results["version_management"]["versions_created"])}

### Version Lineage
{' → '.join(results["version_management"]["version_lineage"])}

## Agent Performance

### Execution Summary
- **Agents Executed:** {results["agent_performance"]["agents_executed"]}
- **Successful Executions:** {results["agent_performance"]["successful_executions"]}
- **Total Processing Time:** {results["agent_performance"]["total_processing_time"]:.2f}s
- **Average Processing Time:** {results["agent_performance"]["average_processing_time"]:.2f}s

### Agent Details
"""

        for agent_detail in results["agent_performance"]["agent_details"]:
            agent_type = agent_detail["agent_type"]
            success = "✅" if agent_detail["success"] else "❌"
            quality_score = agent_detail.get("quality_score", "N/A")
            processing_time = agent_detail["processing_time"]

            content += f"""
#### {agent_type}
- **Status:** {success}
- **Quality Score:** {quality_score}
- **Processing Time:** {processing_time:.2f}s
- **Version Created:** {agent_detail["version_created"]}
"""

        content += f"""
## Recommendations

"""

        if outcome["success"] and outcome["human_handoff"]:
            content += "✅ **Pipeline Success**: Quality targets achieved. Ready for human review and approval.\n\n"
        elif outcome["escalated"]:
            content += "⚠️ **Human Intervention**: Pipeline escalated. Review required for quality issues or plateau.\n\n"
        else:
            content += "❌ **Pipeline Issues**: Processing incomplete. Check agent logs for details.\n\n"

        # Add specific recommendations based on final quality
        if final_assessment:
            overall_score = final_assessment.get('overall_score', 0)
            if overall_score >= 90:
                content += "🎉 **Excellent Quality**: Document exceeds publication standards.\n"
            elif overall_score >= 85:
                content += "✅ **Good Quality**: Document meets professional standards.\n"
            elif overall_score >= 80:
                content += "⚠️ **Acceptable Quality**: Document may benefit from additional review.\n"
            else:
                content += "❌ **Quality Concerns**: Document requires significant improvement.\n"

        content += f"""
## Next Steps

{'1. **Human Review**: Proceed with human reviewer approval process' if outcome['ready_for_review'] else '1. **Technical Review**: Address pipeline issues before proceeding'}
2. **Version Management**: Final version `{results["version_management"]["final_version"]}` ready for use
3. **Quality Tracking**: Monitor quality metrics for future improvements
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def print_pipeline_summary(self, results: Dict):
        """Print concise pipeline summary to console."""
        outcome = results["pipeline_outcome"]
        final_assessment = results["quality_results"]["final_assessment"]

        print(f"📊 PIPELINE SUMMARY")
        print(f"  Status: {'✅ Success' if outcome['success'] else '⚠️ Escalated' if outcome['escalated'] else '❌ Failed'}")
        print(f"  Iterations: {outcome['iterations_completed']}")
        print(f"  Final Version: {results['version_management']['final_version']}")

        if final_assessment:
            overall_score = final_assessment.get('overall_score', 0)
            content_score = final_assessment.get('content_score', 0)
            latex_score = final_assessment.get('latex_score', 0)
            print(f"  Quality Scores: Overall {overall_score}, Content {content_score}, LaTeX {latex_score}")

        print(f"  Human Handoff: {'✅ Ready' if outcome['human_handoff'] else '❌ Not Ready'}")
        print(f"  Report: {self.reports_dir}/{results['pipeline_metadata']['workflow_id']}_pipeline_summary.md")


def main():
    """Run the QA orchestrator agent."""
    import argparse

    parser = argparse.ArgumentParser(description='QA Orchestrator Agent')
    parser.add_argument(
        '--content', '-c',
        default='research_report',
        help='Content source folder (e.g., research_report, magazine)'
    )
    args = parser.parse_args()

    content_source = args.content

    print("[*] Starting QA Orchestrator Agent")
    print("=" * 70)
    print(f"Content source: {content_source}")

    # Initialize agent with content source
    agent = QAOrchestratorAgent(content_source=content_source)

    try:
        # Run complete QA pipeline
        results = agent.orchestrate_qa_pipeline(
            starting_version="v0_original",
            workflow_id="qa_pipeline"
        )

        print("\n" + "=" * 70)
        print("QA Orchestration complete!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()