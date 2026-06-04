type ProfileFormProps = {
  resumeText: string;
  isLoading: boolean;
  isSaving: boolean;
  validationError?: string | null;
  onResumeTextChange: (value: string) => void;
  onSave: () => void;
};

export function ProfileForm({
  resumeText,
  isLoading,
  isSaving,
  validationError,
  onResumeTextChange,
  onSave,
}: ProfileFormProps) {
  return (
    <div className="form">
      <div className="field">
        <label htmlFor="resumeText">Resume text</label>
        <textarea
          id="resumeText"
          onChange={(event) => onResumeTextChange(event.target.value)}
          placeholder="Paste resume text here..."
          value={resumeText}
        />
        <p className="helper-text">Resume text is required. Paste the version you want the analyzer to use right now.</p>
        {validationError ? <p className="field-error">{validationError}</p> : null}
      </div>

      <div>
        <button className="button" disabled={isLoading || isSaving} onClick={onSave} type="button">
          {isSaving ? "Saving..." : "Save Profile"}
        </button>
      </div>
    </div>
  );
}
