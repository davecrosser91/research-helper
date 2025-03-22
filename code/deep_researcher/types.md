# Systematic Review Workflow Documentation

## Overview
The systematic review workflow consists of three main steps:
1. Research Question Formulation
2. Keyword Analysis
3. Abstract Screening

## Step 1: Research Question Formulation 🎯

### Input
```python
class FormulateQuestionInput:
    research_area: str           # The research area to investigate
    constraints: Dict[str, Any]  # Research constraints (e.g., time_frame, focus_areas, scope)
```

### Output
```python
class FormulateQuestionOutput:
    question: ResearchQuestion   # The formulated research question
    validation: Dict[str, bool]  # Validation results against FINER criteria

class ResearchQuestion:
    question: str               # The main research question
    sub_questions: List[str]    # Related sub-questions
    scope: Dict[str, Any]       # Research scope parameters
```

## Step 2: Keyword Analysis 🔍

### Input
```python
# Primary input is the research question string and context
research_question: str          # The main research question
context: Dict[str, Any]        # Additional context (field, sub_questions, constraints)
```

### Output
```python
class SearchStrategy:
    keywords: List[str]         # List of search keywords
    combinations: List[str]     # Boolean combinations of keywords
    constraints: Dict[str, Any] # Search constraints
```

## Step 3: Abstract Screening 📚

### Input
```python
class ScreeningInput:
    papers: List[Dict[str, Any]]  # List of papers to screen
    criteria: Dict[str, Any]      # Screening criteria
    context: Dict[str, Any]       # Research context
```

### Output
```python
class ScreenedPaper:
    paper_id: str                 # Unique identifier for the paper
    title: str                    # Paper title
    authors: List[str]            # List of authors
    abstract: str                 # Paper abstract
    relevance_score: float        # Relevance score between 0 and 1
    inclusion_criteria: Optional[Dict[str, bool]]  # Results for each inclusion criterion
    priority_rank: int            # Priority ranking (1 being highest)
    metadata: Dict[str, Any]      # Additional metadata including rationale
```

## Complete Workflow Output
```python
class WorkflowResult:
    research_question: FormulateQuestionOutput  # Results from step 1
    search_strategy: SearchStrategy            # Results from step 2
    screened_papers: Optional[List[ScreenedPaper]]  # Results from step 3 (if papers provided)
```

## Workflow States
```python
class WorkflowState(Enum):
    INITIALIZING = auto()
    QUESTION_FORMULATION = auto()
    KEYWORD_ANALYSIS = auto()
    ABSTRACT_SCREENING = auto()
    REPORT_GENERATION = auto()
    COMPLETED = auto()
    ERROR = auto()
``` 