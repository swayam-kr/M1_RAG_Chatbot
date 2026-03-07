from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
import datetime

def flatten_dict_to_text(d, prefix=""):
    """
    Recursively flattens a nested dictionary or list into a continuous, readable text string
    optimized for LLM comprehension.
    """
    text_blocks = []
    
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                text_blocks.append(f"{prefix}{k}:")
                text_blocks.append(flatten_dict_to_text(v, prefix + "  "))
            else:
                text_blocks.append(f"{prefix}{k}: {v}")
    elif isinstance(d, list):
        for item in d:
            if isinstance(item, (dict, list)):
                text_blocks.append(flatten_dict_to_text(item, prefix + "- "))
            else:
                text_blocks.append(f"{prefix}- {item}")
    else:
        text_blocks.append(f"{prefix}{d}")
        
    return "\n".join(text_blocks)

def process_and_chunk(data_dict, source_url="Global/AMC"):
    """
    Flattens the data dictionary to text, splits it using LangChain,
    and attaches exact metadata to each chunk.
    """
    raw_text = flatten_dict_to_text(data_dict)
    
    # Target Architecture Configuration: ~500-1000 size, 50-100 overlap
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    texts = text_splitter.split_text(raw_text)
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    chunks = []
    for txt in texts:
        chunks.append({
            "page_content": txt,
            "metadata": {
                "source_url": source_url,
                "scraped_at_timestamp": timestamp,
                "fund_name": data_dict.get("Scheme Name") or data_dict.get("Fund Name") or "Global"
            }
        })
        
    return chunks
