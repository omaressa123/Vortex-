import langchain
print(f"LangChain version: {langchain.__version__}")
print(f"LangChain path: {langchain.__path__}")
try:
    import langchain.chains
    print("langchain.chains imported")
except ImportError as e:
    print(f"Error importing langchain.chains: {e}")
    print("Contents of langchain:")
    print(dir(langchain))
