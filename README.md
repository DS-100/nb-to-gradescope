DS100 Notebook to Gradescope Exporter
=====================================

Converts a notebook with student written answers to a PDF for Gradescope.
Ensures that each question has a constant number of pages.

## Getting Started

```
pip install gs100
```

In Python:

```python
from gs100 import convert
# The num_questions argument is the number of written questions to grade.
# It's optional but recommend to help students debug their notebook
convert('some_notebook.ipynb', num_questions=10)
```
