# Quick Start Guide 🚀

Get started with Accent Coach AI in 5 minutes!

## Prerequisites

- Python 3.8+
- Microphone
- Internet connection

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-groq-api-key-here"
```

Get your free API key at: https://console.groq.com/keys

### 3. Run the App

```bash
streamlit run app.py
```

The app will open at: http://localhost:8501

## First Use

1. **Select a practice text** from the sidebar
2. **Click the microphone** to record
3. **Speak the text** clearly
4. **Click "Analyze"** and wait ~10 seconds
5. **Review your results** in the tabs

## Tips for Best Results

- Speak clearly at normal pace
- Use a quiet environment
- Position mic 6-12 inches away
- Complete the full phrase without pausing
- Try multiple times to track improvement

## Troubleshooting

### Microphone not working?
- Grant browser microphone permissions
- Try Chrome or Firefox
- Check system mic settings

### Slow processing?
- First run downloads models (~2GB)
- Use CUDA GPU if available
- Reduce audio length

### No LLM feedback?
- Check GROQ_API_KEY is correct
- Verify internet connection
- Check API quota

## Next Steps

- Read the full [README.md](README.md)
- Try different difficulty levels
- Experiment with custom texts
- Review technical analysis
- Track your history

## Support

Questions? Check the [README](README.md) or open an issue on GitHub.

---

**Ready to improve your accent?** Let's go! 🎤
