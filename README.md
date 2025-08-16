# 🔄 Round Robin Group Generator

A smart web application that generates optimal student groups while minimizing repeated pairings across multiple weeks. Built with Streamlit and deployed on Streamlit Cloud.

## ✨ Features

- **🔄 Smart Round-Robin Algorithm**: Avoids consecutive week pairings while allowing necessary distant repeats
- **📏 Intelligent Group Sizing**: Maintains proper group sizes (never below target, max +1 for remainders)
- **👥 Dual Input Methods**: Use numbered students or paste actual student names
- **📊 Comprehensive Analytics**: Detailed statistics and visualizations of pairing patterns
- **💾 Multiple Export Formats**: Download results as CSV or Excel files
- **🎯 Flexible Configuration**: Works with any number of students and group sizes
- **📱 Responsive Design**: Works on desktop, tablet, and mobile

## 🚀 Live Demo

**[Try it now on Streamlit Cloud!](https://roundrobin.streamlit.app/)**

## 📖 How to Use

### Method 1: Numbered Students
1. Select "Use Numbers" in the sidebar
2. Enter the number of students (2-100)
3. Set your desired group size
4. Choose number of weeks
5. Click "Generate Groups"

### Method 2: Named Students
1. Select "Paste Names" in the sidebar
2. Paste student names (one per line) in the text area
3. Set your desired group size
4. Choose number of weeks
5. Click "Generate Groups"

### Example Names Input:
```
Alice Johnson
Bob Smith
Charlie Davis
Diana Wilson
Emma Thompson
Frank Miller
Grace Lee
```

## 🧮 Group Sizing Logic

The algorithm intelligently handles any student count:

- **24 students, size 4**: → Groups of 4, 4, 4, 4, 4, 4
- **23 students, size 4**: → Groups of 5, 5, 5, 4, 4
- **26 students, size 4**: → Groups of 5, 5, 4, 4, 4, 4
- **31 students, size 5**: → Groups of 6, 6, 6, 6, 5, 5

*Groups never go below the target size, but get +1 student when needed for remainders.*

## 📊 Understanding the Results

### Four Main Views:

1. **📋 Student View**: See which group each student is in for each week
2. **👥 Group View**: Browse groups by week with student compositions
3. **📈 Statistics**: Analyze pairing patterns and algorithm performance
4. **💾 Download**: Export your results in CSV or Excel format

### Key Metrics:

- **Consecutive Week Repeats**: Should be 0 or very low (most important)
- **Overall Repeated Pairs**: Total pairs that appear more than once (expected)
- **Consecutive Avoidance**: Percentage of pairs that avoid immediate repeats

## 🎯 Algorithm Philosophy

### What It Optimizes For:
- ✅ **Zero consecutive week repeats** (highest priority)
- ✅ **Proper group sizing** (never undersized)
- ✅ **Fair distribution** (students get varied partners over time)

### What It Accepts:
- ✅ **Distant repeats** (unavoidable with many weeks)
- ✅ **Uneven group sizes** (when mathematically necessary)

*This approach is much more practical than trying to avoid ALL repeats, which becomes impossible with multiple weeks.*

## 🔧 Configuration Options

- **Students**: 2-100 (numbered or named)
- **Group Size**: 2-10 students per group
- **Weeks**: 1-20 weeks of scheduling
- **Input Method**: Numbers or pasted names

## 📱 Mobile Friendly

The app works great on mobile devices! Perfect for teachers who need to generate groups on the go.

## 🛠️ Technical Details

- **Built with**: Streamlit, Pandas, Plotly
- **Hosted on**: Streamlit Cloud
- **Algorithm**: Custom round-robin with conflict minimization
- **Export formats**: CSV, Excel (XLSX)

## 🚀 Deployment

This app is deployed on Streamlit Cloud and updates automatically from this GitHub repository.

### To deploy your own version:
1. Fork this repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select your forked repository
5. Set main file path to `roundrobin.py`
6. Deploy!

## 📄 Files

- `roundrobin.py` - Main Streamlit application
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## 🤝 Contributing

Found a bug or have a feature request? Please open an issue or submit a pull request!

## 📜 License

MIT License - Feel free to use, modify, and distribute!

---

**Perfect for**: Teachers, trainers, workshop organizers, team leads, or anyone who needs to create fair, rotating groups over multiple sessions.

**Made with ❤️ and Streamlit**
