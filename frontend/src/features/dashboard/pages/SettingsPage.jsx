import { useWorkspaceContext } from "@app/providers";
import { FeedbackBanner, SettingsPanel } from "@features/dashboard/components";

export function SettingsPage() {
  const { busy, feedback, profileForm, saveSettings, tenantForm, testAuth } = useWorkspaceContext();

  return (
    <>
      {feedback?.message ? <FeedbackBanner feedback={feedback} /> : null}
      <SettingsPanel
        tenantForm={tenantForm}
        profileForm={profileForm}
        onSave={saveSettings}
        onTestAuth={testAuth}
        busy={busy}
      />
    </>
  );
}
