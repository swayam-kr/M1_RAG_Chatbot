import json
from chunker import flatten_dict_to_text, process_and_chunk

def test_flat_text_generation():
    test_data = {
        "Name": "Example Fund",
        "nested": {
            "val1": "foo",
            "val2": "bar"
        },
        "arr": [
            "one",
            "two"
        ]
    }
    
    text = flatten_dict_to_text(test_data)
    
    # Assert formatting structure is linear and readable
    assert "Name: Example Fund" in text
    assert "nested:" in text
    assert "  val1: foo" in text
    assert "arr:" in text
    assert "- one" in text

def test_chunking_constraints():
    test_data = {
        "Scheme Name": "Extremely Large Synthetic Document " * 100, # Will force splitting
        "Another property": "Some other continuous data block " * 50
    }
    
    url = "https://example.com/mock-fund"
    chunks = process_and_chunk(test_data, source_url=url)
    
    assert len(chunks) > 1, f"Expected multiple chunks, but got {len(chunks)}. Splitting failed."
    
    for i, c in enumerate(chunks):
        content = c["page_content"]
        meta = c["metadata"]
        
        # 1. Assert size limit constraint
        assert len(content) <= 800, f"Chunk {i} size exceeded limit of 800: it is {len(content)}"
        
        # 2. Assert metadata properties are always present natively
        assert meta["source_url"] == url, "Source URL lost in chunking."
        assert "scraped_at_timestamp" in meta, "Missing precise ingestion timestamp."
        assert meta["fund_name"] == "Extremely Large Synthetic Document " * 100, "Missing contextual Fund reference."

    print("Phase 3 text and chunking verification tests passed!")

if __name__ == "__main__":
    test_flat_text_generation()
    test_chunking_constraints()
