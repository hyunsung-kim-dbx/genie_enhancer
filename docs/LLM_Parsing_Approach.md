# LLM-Based Parsing: Why It's Better

## The Problem with Fixed Code Parsers

Traditional fixed-code parsers have significant limitations:

❌ **Rigid**: Only handle predefined document formats  
❌ **Brittle**: Break when document structure changes  
❌ **Maintenance**: Require code updates for new formats  
❌ **Limited**: Can't understand context or intent  
❌ **Language-specific**: Struggle with multilingual content  

## The LLM Solution

Using LLM for document parsing provides:

✅ **Flexibility**: Adapts to ANY document format automatically  
✅ **Robustness**: Handles variations in structure and formatting  
✅ **Zero Code Changes**: Improve by refining prompts, not rewriting code  
✅ **Context Understanding**: Understands relationships and intent  
✅ **Multilingual**: Naturally handles Korean, English, or mixed content  
✅ **Future-Proof**: Works with new document types without updates  

## Architecture Comparison

### Fixed Code Approach (Not Recommended)
```
Document → Regex/Pattern Matching → Structured Data
         ↓
    Breaks when format changes
    Requires code updates
    Limited to known patterns
```

### LLM Approach (Recommended) ⭐
```
Document → LLM with Prompt → Structured Data
         ↓
    Adapts automatically
    Improve via prompts
    Understands context
```

## Implementation Strategy

### Skill 1: LLM-Based Parser (Flexible)
- **Technology**: LLM (Databricks agent LLM or external)
- **Input**: Any document format
- **Output**: Structured JSON
- **Improvement**: Refine prompts, add examples

### Skills 2-4: Fixed Code (Reliable)
- **Skill 2**: JSON transformation (deterministic)
- **Skill 3**: API calls (must be reliable)
- **Skill 4**: Validation (must be strict)

## Example: Handling Document Variations

### Fixed Parser Problem
```python
# Fixed parser expects exact format
if "필요한 테이블:" in content:
    tables = extract_tables(content)
else:
    # ❌ Fails - doesn't know what to do
    raise ValueError("Unknown format")
```

### LLM Parser Solution
```python
# LLM understands variations
prompt = f"""
Extract tables from this document.
It might say "필요한 테이블:", "Required tables:", 
"Tables:", or just list them. Extract all table identifiers.

Document: {content}
"""

# ✅ Works with any variation
tables = llm.extract(prompt)
```

## Prompt Design Best Practices

### 1. Clear Instructions
```
Extract tables, columns, joins, and queries from the document.
Output as JSON matching this schema: {...}
```

### 2. Few-Shot Examples
```
Here are examples of good extractions:
Example 1: [shows input → output]
Example 2: [shows input → output]

Now extract from: [your document]
```

### 3. Structured Output
```
Output ONLY valid JSON, no explanations.
Use this exact schema: {...}
```

### 4. Iterative Refinement
```
If extraction fails validation:
1. Show errors to LLM
2. Ask it to fix them
3. Re-extract
```

## Cost & Performance Considerations

### LLM Costs
- **Token Usage**: ~2000-5000 tokens per document
- **Cost**: ~$0.01-0.05 per document (depending on model)
- **Worth It**: Saves hours of manual work

### Performance
- **Speed**: 2-10 seconds per document
- **Accuracy**: 90-95% with good prompts
- **Improvement**: Gets better with prompt refinement

### Optimization
- Cache extractions for unchanged documents
- Batch multiple documents
- Use smaller/faster models for simple docs

## When to Use Each Approach

### Use LLM When:
- ✅ Document formats vary
- ✅ Need to handle multiple languages
- ✅ Want flexibility without code changes
- ✅ Documents have complex structure
- ✅ Need to understand context

### Use Fixed Code When:
- ✅ Document format is 100% standardized
- ✅ Need deterministic output
- ✅ Performance is critical (<100ms)
- ✅ Cost must be zero
- ✅ Format never changes

## Recommendation

**For Genie Space creation: Use LLM-based parsing**

**Reasons:**
1. Your documents vary in format and language
2. You'll add new document types over time
3. Context understanding is important
4. Cost is minimal compared to time saved
5. Can improve without code deployments

## Next Steps

1. **Design prompts** with examples from your documents
2. **Test extraction** on sample documents
3. **Refine prompts** based on results
4. **Add validation** to catch LLM mistakes
5. **Iterate** - improve prompts, not code

---

## Summary

**Fixed code parsers** = Rigid, brittle, requires maintenance  
**LLM parsers** = Flexible, robust, improves via prompts  

For document parsing in Genie Space automation, **LLM is the clear winner**.
