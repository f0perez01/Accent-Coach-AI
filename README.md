# Accent Coach AI 🎙️

Interactive pronunciation practice application for American English with AI-powered feedback.

## Features

- **Real-time Audio Recording**: Record your pronunciation directly in the browser
- **AI-Powered Analysis**: Uses state-of-the-art Wav2Vec2 models for speech recognition
- **Phonetic Comparison**: Word-by-word phonetic analysis
- **LLM Feedback**: Get personalized coaching feedback from AI
- **Multiple Practice Texts**: Curated collection of beginner to advanced phrases
- **Session History**: Track your progress over multiple attempts
- **Detailed Metrics**: Word accuracy, phoneme error rate, and error distribution

## Screenshots

### Main Interface
- Practice text selection
- Real-time audio recording
- Instant pronunciation analysis

### Analysis Results
- **Word Comparison Tab**: Color-coded word-by-word comparison
- **Coach Feedback Tab**: Personalized improvement suggestions
- **Technical Analysis Tab**: Detailed phoneme metrics and error distribution
- **History Tab**: Track your improvement over time

## Installation

### Prerequisites

- Python 3.8 or higher
- Microphone access in your browser
- (Optional) CUDA-capable GPU for faster processing

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/accent-coach-ai.git
cd accent-coach-ai
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### macOS Troubleshooting

- If `pip install -r requirements.txt` fails while building native extensions (errors mentioning missing headers like `<cmath>` or failed `clang++`), install the Xcode Command Line Tools and re-run the install:

```bash
xcode-select --install
# then (after install finishes)
source venv/bin/activate
pip install -r requirements.txt
```

- As an alternative, use `conda` or `mamba` with the `conda-forge` channel to install prebuilt native packages and avoid compilation on macOS:

```bash
conda create -n accent-coach python=3.11
conda activate accent-coach
conda install -c conda-forge python-crfsuite gruut gruut_lang_en soundfile ffmpeg
pip install -r requirements.txt
```

**Note**: Installing PyTorch with CUDA support (optional):
```bash
# For CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Step 4: Configure API Keys

#### Option A: Using Streamlit Secrets (Recommended)

1. Copy the example secrets file:
```bash
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

2. Edit `.streamlit\secrets.toml` and add your API keys:
```toml
GROQ_API_KEY = "your-groq-api-key-here"
HF_API_TOKEN = "your-hf-token-here"  # Optional
```

#### Option B: Using Environment Variables

1. Copy the example env file:
```bash
copy .env.example .env
```

2. Edit `.env` and add your API keys:
```
GROQ_API_KEY=your-groq-api-key-here
HF_API_TOKEN=your-hf-token-here
```

3. Load environment variables before running:
```bash
# Windows
set GROQ_API_KEY=your-key-here

# Linux/Mac
export GROQ_API_KEY=your-key-here
```

### Getting API Keys

- **Groq API Key** (Required for LLM feedback): https://console.groq.com/keys
- **Hugging Face Token** (Optional, for private models): https://huggingface.co/settings/tokens

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Vocabulary Coach MVP

There is a minimal MVP for personalized vocabulary suggestions in `vocab_mvp.py`.

Quick run (inside the repo, with your venv activated):

```bash
pip install streamlit sentence-transformers scikit-learn
streamlit run vocab_mvp.py
python -m streamlit run vocab_mvp.py

```

The app accepts pasted or uploaded text, computes simple lexical metrics, and shows a ranked list of vocabulary suggestions. This is a lightweight prototype for pilot testing.

### Using the Application

1. **Select a Practice Text**
   - Choose a category (Beginner, Intermediate, Advanced, Common Phrases)
   - Select a phrase from the dropdown
   - Or use the "Use custom text" option to enter your own

2. **Configure Settings** (Optional)
   - Open "Advanced Settings" in the sidebar
   - Select ASR model
   - Toggle G2P (Grapheme-to-Phoneme) conversion
   - Enable/disable LLM feedback

3. **Record Your Pronunciation**
   - Click "Record your pronunciation" button
   - Allow microphone access when prompted
   - Speak clearly and naturally
   - Click "Stop recording" when done

4. **Analyze**
   - Click "Analyze Pronunciation" button
   - Wait for processing (typically 5-10 seconds)
   - Review results in the tabs

5. **Review Results**
   - **Word Comparison**: See which words were pronounced correctly
   - **Coach Feedback**: Get AI-generated improvement tips
   - **Technical Analysis**: View detailed metrics and waveform
   - **History**: Compare with previous attempts

## Architecture

### Pipeline Flow

```
Audio Recording (Browser)
    ↓
WAV Conversion (16kHz mono)
    ↓
ASR Transcription (Wav2Vec2)
    ↓
Phoneme Generation (gruut)
    ↓
Sequence Alignment (Needleman-Wunsch)
    ↓
Word-by-Word Comparison
    ↓
LLM Feedback (Groq)
    ↓
Results Display
```

### Key Components

- **ASR Models**:
  - `facebook/wav2vec2-large-960h` (orthographic, recommended)
  - `mrrubino/wav2vec2-large-xlsr-53-l2-arctic-phoneme` (phonetic)

- **Phoneme Generation**: gruut library for IPA phoneme conversion

- **Alignment Algorithm**: Needleman-Wunsch for optimal sequence alignment

- **LLM**: Groq API with `llama-3.1-8b-instant` for feedback

## CLI Tool

The project also includes a command-line interface for batch processing:

```bash
python run_mdd.py --audio your_audio.wav --text "Your reference text"
```

### CLI Options

```
--audio, -a          Path to audio file (required)
--text, -t           Reference text (optional, interactive if not provided)
--model, -m          ASR model name
--lang               Language code (default: en-us)
--no-llm             Disable LLM feedback
--no-g2p             Disable G2P conversion
--force-phoneme-model Use phonetic model
--emit-json          Export results to JSON file
```

## Configuration

### Streamlit Configuration

Create `.streamlit/config.toml` to customize the app:

```toml
[theme]
primaryColor = "#3498db"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 50
enableXsrfProtection = true
```

### Practice Texts

Edit the `PRACTICE_TEXTS` dictionary in `app.py` to add custom practice phrases:

```python
PRACTICE_TEXTS = {
    "Your Category": [
        "Your custom phrase 1",
        "Your custom phrase 2",
    ]
}
```

## Troubleshooting

### Audio Recording Issues

**Problem**: Microphone not working
- **Solution**: Grant browser microphone permissions
- Check browser console for errors
- Try a different browser (Chrome/Firefox recommended)

### Model Loading Issues

**Problem**: Out of memory errors
- **Solution**: Use CPU instead of CUDA
- Reduce batch size
- Close other applications

**Problem**: Model download fails
- **Solution**: Check internet connection
- Verify HuggingFace token if using private models
- Try downloading manually: `huggingface-cli download facebook/wav2vec2-large-960h`

### LLM Feedback Issues

**Problem**: No feedback generated
- **Solution**: Verify GROQ_API_KEY is set correctly
- Check API quota/limits
- Enable debug mode to see error messages

### Performance Issues

**Problem**: Slow processing
- **Solution**:
  - Use CUDA if available
  - Reduce audio length
  - Use smaller/faster model
  - Close unnecessary browser tabs

## Development

### Project Structure

```
Accent-Coach-AI/
├── app.py                      # Streamlit application
├── run_mdd.py                  # CLI tool
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .streamlit/
│   ├── secrets.toml.example    # API key template
│   └── config.toml             # Streamlit config
├── .env.example                # Environment variables template
└── prompt_streamlit_interface.md  # Design specifications
```

### Adding New Features

1. **New Practice Texts**: Edit `PRACTICE_TEXTS` in `app.py`
2. **New Models**: Add to `MODEL_OPTIONS` dictionary
3. **Custom Metrics**: Modify `calculate_metrics()` function
4. **UI Customization**: Edit Streamlit components in `main()` function

## Performance Optimization

- **Model Caching**: Models are cached with `@st.cache_resource`
- **Audio Processing**: Optimized with torchaudio/librosa
- **Lazy Loading**: Components load only when needed
- **Session State**: Efficient history management

## Privacy & Security

- **Audio Data**: Only stored in session memory, not persisted
- **API Keys**: Stored securely in secrets.toml (not committed to git)
- **No Data Collection**: All processing happens locally
- **Browser Permissions**: Only microphone access required

## License

MIT License - see LICENSE file for details

## Credits

- **ASR Models**: Facebook AI Research (Wav2Vec2)
- **Phoneme Generation**: gruut library
- **LLM**: Groq API (Llama 3.1)
- **UI Framework**: Streamlit

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation

## Roadmap

- [ ] Multi-language support
- [ ] TTS for reference audio
- [ ] Advanced visualizations
- [ ] User authentication
- [ ] Progress tracking over time
- [ ] Export to PDF reports
- [ ] Mobile app version

## Acknowledgments

Built with Streamlit, PyTorch, Transformers, and Groq API.

---

**Happy Practicing!** 🎤
