# Quick Start Guide

Get up and running with the AFL++ + PPO fuzzing framework in 5 minutes!

## Prerequisites Check

```bash
# Check if AFL++ is installed
afl-fuzz -h

# Check Python version (need 3.8+)
python3 --version

# Check available disk space (need 20GB+)
df -h .
```

## Installation (2 minutes)

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Setup seed inputs
mkdir -p data/inputs
echo "test" > data/inputs/seed1.txt
echo "hello" > data/inputs/seed2.txt
```

## Run Your First Experiment (1 minute to start)

### Option 1: Using the Quick Start Script (Easiest)

```bash
./run_experiment.sh /path/to/your/binary 1800
```

This runs a 30-minute comparison experiment (15 min baseline + 15 min PPO).

### Option 2: Manual Run

```bash
cd src
python experiment_runner.py /path/to/your/binary --mode comparison --duration 1800
```

## View Results

```bash
# Generate graphs
cd visualization
python graph_generator.py

# View graphs
ls ../graphs/*.png

# Read summary
cat ../data/results/comparison/paper_results.txt
```

## Example with Vulnerable Program

Test the framework with a simple vulnerable program:

```bash
# Create test program
cat > test_target.c << 'EOF'
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    char buf[100];
    if (argc < 2) return 1;

    FILE *f = fopen(argv[1], "r");
    if (!f) return 1;

    fgets(buf, 200, f);  // Buffer overflow vulnerability!

    if (strstr(buf, "CRASH")) {
        int *p = NULL;
        *p = 42;  // Intentional crash
    }

    printf("OK\n");
    fclose(f);
    return 0;
}
EOF

# Compile
gcc test_target.c -o test_target

# Run experiment (5 minute test)
./run_experiment.sh ./test_target 300
```

## Understanding Your Results

After the experiment, you'll see:

```
FUZZING COMPARISON SUMMARY
==========================================================

AFL++ (Baseline):
  Coverage: 45.20%
  Crashes: 8
  Avg Speed: 234.5 exec/sec
  Unique Paths: 523

AFL++ + PPO:
  Coverage: 62.80%
  Crashes: 15
  Avg Speed: 352.1 exec/sec
  Unique Paths: 847

Improvements (PPO vs Baseline):
  Coverage: +38.9%
  Crashes: +87.5%
  Speed: +50.2%
  Paths: +62.0%
```

## Common Issues

**AFL++ not found:**
```bash
# Install AFL++
git clone https://github.com/AFLplusplus/AFLplusplus
cd AFLplusplus
make distrib
sudo make install
```

**PyTorch installation fails:**
```bash
# Use CPU-only version
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Permission denied:**
```bash
chmod +x run_experiment.sh
```

## Next Steps

1. **Longer experiments**: Increase duration for better results
   ```bash
   ./run_experiment.sh target 7200  # 2 hours per mode
   ```

2. **Custom configuration**: Edit `config/afl_config.yaml` and `config/ppo_config.yaml`

3. **Multiple targets**: Test different binaries

4. **Analysis**: Generate detailed reports
   ```bash
   cd visualization
   python report_generator.py
   ```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./run_experiment.sh target 3600` | Full comparison (1hr each) |
| `python experiment_runner.py target --mode baseline` | Baseline only |
| `python experiment_runner.py target --mode ppo` | PPO only |
| `python graph_generator.py` | Generate graphs |
| `python report_generator.py` | Generate reports |

## Getting Help

- Check `README.md` for detailed documentation
- Review logs in `data/results/`
- Ensure AFL++ is properly installed
- Verify target binary is executable

## Pro Tips

1. **Start with short experiments** (15-30 min) to verify everything works
2. **Use multiple seed inputs** for better coverage
3. **Monitor system resources** during fuzzing
4. **Save PPO models** for transfer learning experiments
5. **Compare multiple binaries** to validate improvements

---

Happy Fuzzing! 🐛🔍
