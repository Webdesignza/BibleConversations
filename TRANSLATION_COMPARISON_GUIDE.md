# 🔄 Translation Comparison Feature - Implementation Guide

This guide shows you how to add Bible translation comparison to your existing system **without breaking anything**.

---

## 📋 What This Feature Does

Users can:
- ✅ Select 2-4 translations to compare (e.g., KJV, NIV, ESV)
- ✅ Ask a question once and see how all selected translations phrase it
- ✅ Get objective side-by-side comparison without interpretation
- ✅ Toggle between single translation mode and comparison mode
- ✅ Use voice interface for both modes

---

## 🛠️ Step 1: Update RAG Service

Open `app/services/rag_service.py` and add two new methods to the `RAGService` class.

### Add After Existing `query()` Method:

```python
def compare_translations(self, question: str, translation_ids: List[str], k: int = None) -> Dict:
    """
    Compare the same passage across multiple Bible translations
    """
    # [Copy code from bible_rag_comparison artifact]
```

```python
def _build_comparison_prompt(self, question: str, comparisons: List[Dict]) -> str:
    """Build prompt for comparing multiple translations"""
    # [Copy code from bible_rag_comparison artifact]
```

**Location:** Add these at the end of the `RAGService` class, before the `get_rag_service()` function.

---

## 🛠️ Step 2: Add API Endpoint

Open `app/api/routes/chat.py` and add the comparison endpoint.

### Add After Existing Imports:

```python
from typing import List
from pydantic import BaseModel
```

### Add New Request Model:

```python
class CompareRequest(BaseModel):
    """Request model for translation comparison"""
    question: str
    translation_ids: List[str]
    k: int = 3
    include_chunks: bool = False
```

### Add New Endpoint:

```python
@router.post("/compare")
async def compare_translations(
    request: CompareRequest,
    token: str = Depends(verify_token)
):
    # [Copy code from bible_compare_route artifact]
```

**Location:** Add after your existing `/api/chat` POST endpoint.

---

## 🛠️ Step 3: Update Widget JavaScript

Open `static/bible-widget.js` and add comparison functionality.

### Add to State Variables (around line 15):

```javascript
compareMode: false,
selectedTranslationsForCompare: [],
```

### Add New Methods (after existing methods):

1. `toggleCompareMode()`
2. `updateCompareUI()`
3. `toggleTranslationForCompare(translationId)`

[Copy all three methods from bible_widget_comparison artifact]

### Update Existing `getChatResponse()` Method:

Replace your existing `getChatResponse()` with the updated version that handles both single and compare modes.

[Copy from bible_widget_comparison artifact]

---

## 🛠️ Step 4: Update Widget HTML

In `static/bible-widget.js`, find the `createPopup()` method and update the HTML.

### Add After Translation Selector (around line 180):

```html
<button id="compare-mode-btn" 
        class="bible-btn-action secondary" 
        style="margin: 10px 0;"
        onclick="BibleWidget.toggleCompareMode()">
    🔄 Compare Translations
</button>

<div id="compare-selections" 
     style="display:none; 
            padding: 15px; 
            background: #f0f9ff; 
            border-radius: 8px; 
            margin-bottom: 15px; 
            text-align: left;">
</div>
```

### Add CSS (in `injectStyles()` method):

```css
.bible-btn-action.active {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
}

#compare-selections label {
    display: block;
    padding: 8px;
    border-radius: 5px;
    transition: background 0.2s;
}

#compare-selections label:hover {
    background: rgba(30, 58, 138, 0.1);
}

#compare-selections input[type="checkbox"] {
    margin-right: 8px;
}
```

---

## ✅ Step 5: Test Locally

### Start Your Server:

```bash
python -m uvicorn app.main:app --reload --port 8009
```

### Test Single Translation Mode (Existing):

1. Open http://localhost:8009/agent
2. Select one translation (e.g., KJV)
3. Click "Start"
4. Ask: "What does John 3:16 say?"
5. Should work as before ✅

### Test Comparison Mode (New):

1. Click "🔄 Compare Translations" button
2. Select 2-3 translations (checkboxes appear)
3. Click "Start"
4. Ask: "Compare John 3:16"
5. Should hear comparison of all selected translations ✅

---

## 🚀 Step 6: Deploy to Railway

```bash
# Commit all changes
git add app/services/rag_service.py
git add app/api/routes/chat.py
git add static/bible-widget.js
git commit -m "Add translation comparison feature"
git push origin main
```

Railway will automatically deploy the updates!

---

## 📖 How Users Will Use It

### Single Translation Mode (Default):
1. User selects ONE translation from dropdown
2. Clicks "Start"
3. Asks questions → gets answers from that translation

### Comparison Mode (New):
1. User clicks "🔄 Compare Translations" button
2. Checkboxes appear showing all available translations
3. User selects 2-4 translations to compare
4. Clicks "Start"
5. Asks question → gets side-by-side comparison

### Example Comparison Output:

**User asks:** "What does John 3:16 say?"

**AI responds:**
> "Here's John 3:16 across the translations you selected:
> 
> **King James Version (KJV):** For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life.
> 
> **New International Version (NIV):** For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.
> 
> **English Standard Version (ESV):** For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life.
> 
> **Key differences:** The KJV uses 'only begotten Son' and 'whosoever believeth' with older English phrasing, while the NIV and ESV use modern language with 'one and only Son' and 'whoever believes.'"

---

## 🎯 Benefits of This Approach

✅ **No Breaking Changes** - All existing functionality stays the same
✅ **Optional Feature** - Users can ignore it and use single mode
✅ **Easy Toggle** - One button to switch between modes
✅ **Voice Compatible** - Works with the voice interface
✅ **Objective Comparison** - No theological bias, just textual differences
✅ **Scalable** - Supports 2-4 translations at once

---

## 🐛 Troubleshooting

### Comparison Button Doesn't Appear
- Check that you added the HTML in `createPopup()`
- Check browser console for JavaScript errors

### Comparison Request Fails
- Verify the `/api/chat/compare` endpoint exists in `chat.py`
- Check Railway logs for errors
- Verify selected translations have data uploaded

### Checkboxes Don't Work
- Check that `toggleTranslationForCompare()` is defined
- Check browser console for errors
- Verify `BibleWidget` object has the new methods

---

## 📞 Need Help?

- Check Railway logs: `Observability` tab
- Test endpoints directly: `/docs` (Swagger UI)
- Verify translations exist: `/api/translations/list`

---

**You're done!** Users can now compare Bible translations side-by-side! 🎉