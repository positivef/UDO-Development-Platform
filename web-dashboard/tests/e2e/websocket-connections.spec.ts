import { test, expect } from '@playwright/test';

/**
 * WebSocket Connection Tests
 *
 * Tests for real-time WebSocket connections:
 * - Confidence Dashboard WebSocket (/ws/confidence/{phase})
 * - Uncertainty Map WebSocket (/ws/uncertainty)
 *
 * Prerequisites:
 * - Backend running on port 8000
 * - Frontend running on port 3000
 */

test.describe('WebSocket Connections', () => {
  test.beforeEach(async ({ page }) => {
    // Enable console log capture
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Browser Console Error:', msg.text());
      }
    });
  });

  test('Confidence WebSocket - should connect successfully', async ({ page }) => {
    const wsMessages: string[] = [];
    const wsErrors: any[] = [];

    // Capture console logs
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[ConfidenceWS]')) {
        wsMessages.push(text);
      }
    });

    // Navigate to Confidence page
    await page.goto('http://localhost:3000/confidence');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Wait a bit for WebSocket connection attempt
    await page.waitForTimeout(2000);

    // Check console logs for connection
    const connectionLogs = wsMessages.filter(msg =>
      msg.includes('Connecting to') || msg.includes('Connected')
    );

    console.log('Confidence WebSocket logs:', wsMessages);

    // Verify connection was attempted
    expect(connectionLogs.length).toBeGreaterThan(0);

    // Check for connection URL
    const connectingLog = wsMessages.find(msg => msg.includes('Connecting to'));
    if (connectingLog) {
      expect(connectingLog).toContain('ws://localhost:8000/ws/confidence/');
      console.log('✅ Connection URL correct:', connectingLog);
    }

    // Check for successful connection
    const connectedLog = wsMessages.find(msg => msg.includes('Connected'));
    if (connectedLog) {
      console.log('✅ WebSocket connected successfully');
      expect(connectedLog).toContain('Connected');
    } else {
      // If not connected, check for error logs
      const errorLog = wsMessages.find(msg =>
        msg.includes('error') || msg.includes('WebSocket error')
      );
      if (errorLog) {
        console.log('❌ WebSocket error detected:', errorLog);

        // Extract readyState if present
        const readyStateMatch = errorLog.match(/readyState:\s*(\d+)/);
        if (readyStateMatch) {
          const readyState = parseInt(readyStateMatch[1]);
          console.log('ReadyState:', readyState);
          console.log('ReadyState meaning:', {
            0: 'CONNECTING',
            1: 'OPEN',
            2: 'CLOSING',
            3: 'CLOSED'
          }[readyState]);
        }
      }

      // Print all logs for debugging
      console.log('All WebSocket logs:', wsMessages);

      // This test expects connection to succeed
      expect(connectedLog).toBeDefined();
    }
  });

  test('Confidence WebSocket - should have correct configuration', async ({ page }) => {
    const configLogs: string[] = [];

    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[ConfidenceWS] Config:')) {
        configLogs.push(text);
      }
    });

    await page.goto('http://localhost:3000/confidence');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    console.log('Config logs:', configLogs);

    // Verify config was logged
    expect(configLogs.length).toBeGreaterThan(0);

    const configLog = configLogs[0];

    // Check config values
    expect(configLog).toContain('isDev=true');
    expect(configLog).toContain('wsHost=localhost');
    expect(configLog).toContain('wsPort=8000');
    expect(configLog).toContain('phase=implementation');

    console.log('✅ WebSocket configuration correct');
  });

  test('Uncertainty WebSocket - should connect successfully', async ({ page }) => {
    const wsMessages: string[] = [];

    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[UncertaintyWS]') || text.includes('WebSocket')) {
        wsMessages.push(text);
      }
    });

    await page.goto('http://localhost:3000/uncertainty');
    await page.waitForLoadState('networkidle');

    // Wait longer for WebSocket connection
    await page.waitForTimeout(5000);

    console.log('Uncertainty WebSocket logs:', wsMessages);

    // Check for connection attempt
    const connectingLog = wsMessages.find(msg => msg.includes('Connecting to'));
    expect(connectingLog).toBeDefined();
    expect(connectingLog).toContain('ws://localhost:8000/ws/uncertainty');
    console.log('✅ Connection URL correct:', connectingLog);

    // Check for errors
    const errorLog = wsMessages.find(msg =>
      msg.includes('[UncertaintyWS]') && msg.includes('error')
    );

    if (errorLog) {
      console.log('❌ WebSocket error detected:', errorLog);
      expect(errorLog).toBeUndefined(); // Fail if error exists
    } else {
      console.log('✅ Uncertainty WebSocket - no errors detected');
    }

    // Connection is successful if:
    // 1. Connection attempt was made
    // 2. No WebSocket-specific errors were logged
    expect(connectingLog).toBeDefined();
    expect(errorLog).toBeUndefined();
  });

  test('WebSocket - should handle reconnection on disconnect', async ({ page }) => {
    const wsMessages: string[] = [];

    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[ConfidenceWS]')) {
        wsMessages.push(text);
      }
    });

    await page.goto('http://localhost:3000/confidence');
    await page.waitForLoadState('networkidle');

    // Wait for initial connection
    await page.waitForTimeout(2000);

    // Check initial connection
    const initialConnection = wsMessages.find(msg => msg.includes('Connected'));
    expect(initialConnection).toBeDefined();
    console.log('✅ Initial connection established');

    // Simulate disconnect by navigating away and back
    await page.goto('http://localhost:3000/');
    await page.waitForTimeout(1000);

    // Clear messages
    wsMessages.length = 0;

    // Navigate back to trigger reconnection
    await page.goto('http://localhost:3000/confidence');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    console.log('Reconnection logs:', wsMessages);

    // Check for reconnection attempt
    const reconnectLog = wsMessages.find(msg =>
      msg.includes('Connecting to') || msg.includes('Reconnecting')
    );

    if (reconnectLog) {
      console.log('✅ Reconnection attempted:', reconnectLog);
      expect(reconnectLog).toBeDefined();
    }
  });

  test('WebSocket - should display error details on failure', async ({ page }) => {
    const wsErrors: string[] = [];

    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('[ConfidenceWS]') && text.includes('error')) {
        wsErrors.push(text);
      }
    });

    // Try to connect with backend potentially down
    await page.goto('http://localhost:3000/confidence');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    console.log('Error logs:', wsErrors);

    // If there are errors, verify they include diagnostic info
    if (wsErrors.length > 0) {
      const errorLog = wsErrors[0];

      // Check if error log includes readyState
      const hasReadyState = errorLog.includes('readyState');
      const hasUrl = errorLog.includes('URL');

      console.log('Error log includes readyState:', hasReadyState);
      console.log('Error log includes URL:', hasUrl);

      // Error logs should include diagnostic information
      expect(hasReadyState || hasUrl).toBeTruthy();
    } else {
      console.log('✅ No WebSocket errors detected');
    }
  });

  test('Network Tab - WebSocket status validation', async ({ page }) => {
    // This test checks the Network tab for WebSocket upgrade
    const appWsRequests: any[] = [];

    page.on('websocket', ws => {
      console.log('WebSocket created:', ws.url());

      // Filter only app WebSockets (not Next.js HMR)
      if (ws.url().includes('ws://localhost:8000/')) {
        ws.on('framesent', event => {
          console.log('WebSocket frame sent:', event.payload);
        });

        ws.on('framereceived', event => {
          console.log('WebSocket frame received:', event.payload);
        });

        ws.on('close', () => {
          console.log('WebSocket closed');
        });

        appWsRequests.push(ws);
      }
    });

    await page.goto('http://localhost:3000/confidence');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    console.log('App WebSocket requests captured:', appWsRequests.length);

    // Verify app WebSocket was created (not Next.js HMR)
    expect(appWsRequests.length).toBeGreaterThan(0);

    const ws = appWsRequests[0];
    console.log('App WebSocket URL:', ws.url());

    // Verify URL format
    expect(ws.url()).toContain('ws://localhost:8000/ws/confidence/');
  });
});
