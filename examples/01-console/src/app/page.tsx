"use client";

import {
  ConsoleTemplate,
  FullScreenContainer,
  ThemeProvider,
} from "@pipecat-ai/voice-ui-kit";

export default function Home() {
  return (
    <ThemeProvider>
      <FullScreenContainer>
        <ConsoleTemplate
          transportType="smallwebrtc"
          connectParams={{
            connectionUrl: "/api/offer",
          }}
          // Camera control will be visible but starts OFF by default
          // Remove noUserVideo to show the camera toggle
        />
      </FullScreenContainer>
    </ThemeProvider>
  );
}
