# Answer keys and checkers

Two optional callables make the vote and the filter sharper. Neither may read the label.

## `answer_key(prediction) -> hashable | None`

Decides when two forms "give the same answer". The default lower-cases the output, removes punctuation and articles, and
collapses whitespace. Pass your own when the task has a canonical form:

=== "Math"

    ```python
    import re

    def math_key(pred):
        s = str(pred.answer)
        m = re.findall(r"\\boxed\{(.*)\}", s)
        s = (m[-1] if m else s).replace("$", "").replace(" ", "").rstrip(".")
        return str(int(s)) if re.fullmatch(r"-?\d+", s) else s.lower()
    ```

=== "Multiple choice"

    ```python
    def letter_key(pred):
        m = re.match(r"^\W*([ABCD])\b", str(pred.answer).strip())
        return m.group(1) if m else None
    ```

=== "Text-to-SQL"

    ```python
    def sql_key(pred):
        rows = run_readonly(pred.answer)          # your executor; None if the query fails
        return None if rows is None else hash(frozenset(map(tuple, rows)))
    ```

Returning `None` means "no usable answer": the form is treated like a broken output.

## `checker(inputs, prediction) -> bool | None`

A deterministic test that needs no labels. Forms that fail it are dropped before the vote; if every form fails, all are
kept. Return `None` when the check does not apply.

```python
def public_tests(inputs, pred):
    return run_public_tests(inputs["question"], pred.answer)   # True / False
```

Good checkers: the statement's public unit tests for code, "the SQL query runs and returns rows", a validator of the
constraints stated in a planning problem. In the research evaluation they added about +0.3 pp on top of the vote; the
layer works without them.
