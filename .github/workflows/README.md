# GitHub Actions CI/CD Workflows

This directory contains automated testing and deployment workflows for the UDO Development Platform.

## 📋 Available Workflows

### 1. PR Tests (`pr-tests.yml`)

**Trigger**: Pull requests to `main` branch, pushes to `main`

**Purpose**: Validate code changes before merging

**Jobs**:
- **Backend Tests** (496 tests)
  - Python 3.13 + pytest
  - Coverage reporting (Codecov)
  - Parallel test execution (`-n auto`)
  - FastAPI application tests

- **E2E Tests** (18 tests)
  - Playwright (Chromium only for PR speed)
  - Next.js 16 build validation
  - Backend + Frontend integration
  - Screenshot capture on failure

- **Test Summary**
  - Combined results reporting
  - GitHub Actions summary display

**Duration**: ~5-7 minutes

**Caching**:
- Python pip dependencies
- Node.js npm dependencies

---

### 2. Nightly Tests (`nightly-tests.yml`)

**Trigger**:
- Scheduled: 2 AM UTC daily
- Manual: `workflow_dispatch`

**Purpose**: Comprehensive regression testing across all browsers

**Jobs**:
- **Full E2E Suite** (54 tests)
  - Matrix strategy: Chromium, Firefox, Webkit
  - 18 tests × 3 browsers = 54 total
  - Cross-browser compatibility validation

- **Backend Regression** (496 tests)
  - Full test suite with coverage
  - HTML coverage report generation
  - Parallel execution

- **Performance Benchmarks**
  - DAG performance (1,000 tasks <50ms)
  - Circuit Breaker validation
  - Cache Manager tests

**Duration**: ~15-20 minutes

**Artifacts**:
- Playwright reports (30-day retention)
- Coverage HTML reports (30-day retention)
- Screenshots on failure (7-day retention)

---

## 🚀 Usage

### Manual Trigger (Nightly Tests)

```bash
# Via GitHub CLI
gh workflow run nightly-tests.yml

# Via GitHub UI
Actions → Nightly Regression Tests → Run workflow
```

### Local Testing Simulation

**Backend tests**:
```bash
python -m pytest backend/tests/ -v --cov=backend --cov-report=term -n auto
```

**E2E tests**:
```bash
cd web-dashboard
npm run build
npm run start &
npx playwright test --project=chromium
```

---

## 📊 Success Criteria

### PR Tests
- ✅ All 496 backend tests passing
- ✅ All 18 E2E tests passing (Chromium)
- ✅ No coverage regression
- ✅ Build succeeds

### Nightly Tests
- ✅ All 54 E2E tests passing (3 browsers)
- ✅ All 496 backend tests passing
- ✅ Performance benchmarks meet targets:
  - DAG: <50ms for 1,000 tasks
  - Circuit Breaker: All states working
  - Cache Manager: 50MB limit + LRU

---

## 🔧 Configuration

### Environment Variables

None required currently. All tests use mock data and in-memory databases.

### Secrets

- `CODECOV_TOKEN`: (Optional) For coverage reporting to Codecov

### Caching Strategy

**Python dependencies**:
- Cache key: `pip-${{ hashFiles('**/requirements.txt') }}`
- Reduces install time: ~2 minutes → ~30 seconds

**Node.js dependencies**:
- Cache key: `npm-${{ hashFiles('**/package-lock.json') }}`
- Reduces install time: ~1 minute → ~10 seconds

---

## 📈 Monitoring

### GitHub Actions Dashboard

Navigate to: **Actions** tab → Select workflow

**Key metrics**:
- Success rate (target: >95%)
- Duration trend
- Failure patterns

### Notifications

**On failure**:
- GitHub Actions summary shows failed jobs
- Artifacts uploaded for debugging
- Manual review required

---

## 🐛 Troubleshooting

### Common Issues

**1. E2E tests timeout**
- Check if backend server started (sleep 10s)
- Verify Next.js build succeeded
- Review Playwright timeout settings (60s)

**2. Backend tests fail**
- Check Python version (3.13 required)
- Verify all dependencies installed
- Review PYTHONPATH configuration

**3. Cache issues**
- Clear cache: Settings → Actions → Caches → Delete
- Re-run workflow

**4. Browser installation fails**
- Playwright uses `--with-deps` for system dependencies
- Ubuntu runners should have all required libs

---

## 📝 Maintenance

### Weekly
- Review test execution times
- Check artifact storage usage
- Monitor success rates

### Monthly
- Update browser versions (Playwright auto-updates)
- Review and archive old artifacts
- Optimize cache strategies

### Quarterly
- Evaluate CI/CD costs
- Consider additional test parallelization
- Review coverage thresholds

---

## 🎯 Future Enhancements

### Planned
1. **Visual Regression Testing**
   - Percy or Chromatic integration
   - Automated screenshot comparison

2. **Performance Budget CI**
   - Lighthouse CI integration
   - Automatic performance regression detection

3. **Security Scanning**
   - Dependency vulnerability checks (Dependabot)
   - SAST/DAST integration

4. **Deploy Previews**
   - Vercel/Netlify integration for PR previews
   - Automatic deployment on merge

---

## 📚 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Playwright CI Guide](https://playwright.dev/docs/ci)
- [pytest Documentation](https://docs.pytest.org/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

---

**Last Updated**: 2025-12-23
**Maintained By**: Development Team
**Questions**: Create an issue or ask in #development channel
