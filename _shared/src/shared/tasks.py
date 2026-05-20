"""Canonical task definitions — identical inputs across all frameworks."""

TASKS = {
    "augmented_llm": {
        "description": "Q&A with tool use: weather query requiring tool call + recommendation",
        "input": {"query": "What is the current weather in Tokyo and what should I wear?"},
        "tools_required": ["get_weather"],
        "grading": "Must call get_weather tool AND produce clothing recommendation",
    },
    "prompt_chaining": {
        "description": "Summarize an English paragraph to 2 sentences, then translate to Spanish",
        "input": {
            "text": (
                "WebAssembly, often abbreviated as Wasm, is a binary instruction format designed for "
                "a stack-based virtual machine. It serves as a portable compilation target for programming "
                "languages, enabling deployment on the web for client and server applications. Wasm is "
                "designed to maintain the security properties of the web while being fast, compact, and "
                "platform-independent. Major browsers including Chrome, Firefox, Safari, and Edge all "
                "support WebAssembly natively. Beyond the browser, projects like WASI are extending "
                "WebAssembly to server-side and edge computing environments, opening new possibilities "
                "for portable, sandboxed execution of code across diverse platforms."
            ),
            "target_language": "Spanish",
        },
        "tools_required": [],
        "grading": "Output must contain a 2-sentence English summary AND a Spanish translation",
    },
    "routing": {
        "description": "Classify a support ticket and route to specialized handler",
        "input": {"message": "I was charged twice for my subscription last month"},
        "tools_required": [],
        "grading": "Must classify as 'billing' and produce a billing-specific response",
    },
    "parallelization": {
        "description": "Multi-aspect code review: correctness, performance, and style",
        "input": {
            "code": '''def find_duplicates(lst):
    duplicates = []
    for i in range(len(lst)):
        for j in range(len(lst)):
            if i != j and lst[i] == lst[j]:
                if lst[i] not in duplicates:
                    duplicates.append(lst[i])
    return duplicates
'''
        },
        "tools_required": [],
        "grading": "Must identify: O(n^2) inefficiency, duplicate detection bug (j should start at i+1), and style issues",
    },
    "orchestrator_workers": {
        "description": "Research report on a topic with dynamic subtopic delegation",
        "input": {"topic": "Impact of WebAssembly on server-side computing"},
        "tools_required": ["web_search"],
        "grading": "Must cover >=3 subtopics, have intro + conclusion, cite specific technologies",
    },
    "evaluator_optimizer": {
        "description": "Generate a haiku about autumn, iteratively refine until valid 5-7-5",
        "input": {"theme": "autumn", "max_iterations": 5},
        "tools_required": [],
        "grading": "Valid 5-7-5 syllable structure + theme relevance. Fewer iterations = better",
    },
    "customer_support": {
        "description": "Order troubleshooting with tool access",
        "input": {
            "message": "My order #12345 hasn't arrived and tracking shows stuck in transit for 5 days"
        },
        "tools_required": ["lookup_order", "check_tracking", "issue_refund", "escalate", "search_knowledge_base"],
        "grading": "Must call lookup_order + check_tracking, offer resolution, not hallucinate order details",
    },
    "coding_agent": {
        "description": "Fix a buggy Python function to pass the provided test",
        "input": {
            "buggy_code": '''def merge_sorted(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    return result
''',
            "test_code": '''def test_merge_sorted():
    assert merge_sorted([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
    assert merge_sorted([1, 2], [3, 4, 5]) == [1, 2, 3, 4, 5]
    assert merge_sorted([], [1, 2]) == [1, 2]
    assert merge_sorted([1], []) == [1]
''',
            "expected_fix": "Append remaining elements from both lists after the while loop",
        },
        "tools_required": ["run_python_code"],
        "grading": "Fix must pass all tests. Fewer lines changed = better",
    },
}
