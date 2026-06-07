/**
 * Refresh route - triggers data sync from Tradetron API
 * POST /api/refresh - Start refresh process
 */

const express = require('express');
const { execFile } = require('child_process');
const path = require('path');

const router = express.Router();

/**
 * POST /api/refresh
 * Trigger new_sc_update.py to fetch fresh data from Tradetron
 */
router.post('/', async (req, res) => {
  try {
    console.log('\n' + '='.repeat(70));
    console.log('🔄 REFRESH TRIGGERED via API');
    console.log('='.repeat(70));

    // Path to new_sc_update.py
    const scriptPath = path.join(
      __dirname,
      '..',
      '..',
      '..',
      'AlphaMetrix.In',
      'One time Extraction',
      'src',
      'new_sc_update.py'
    );

    console.log(`📝 Script path: ${scriptPath}`);

    // Execute Python script
    res.json({
      status: 'refresh_started',
      message: 'Data refresh process initiated. Check server logs for progress.',
      timestamp: new Date().toISOString()
    });

    // Run script asynchronously (don't wait for completion)
    // In production, you'd want to queue this or use a job system
    execFile('python', [scriptPath], (error, stdout, stderr) => {
      if (error) {
        console.error('❌ Refresh failed:', error.message);
        if (stderr) console.error('STDERR:', stderr);
        return;
      }

      console.log('✅ Refresh completed successfully');
      if (stdout) console.log(stdout);

      console.log('='.repeat(70));
    });
  } catch (error) {
    console.error('Error starting refresh:', error.message);
    res.status(500).json({
      error: 'Failed to start refresh process',
      message: error.message
    });
  }
});

module.exports = router;
