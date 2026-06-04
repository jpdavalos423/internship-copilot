type JobUrlFormProps = {
  isSaving: boolean;
  url: string;
  validationError?: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export function JobUrlForm({ isSaving, url, validationError, onChange, onSubmit }: JobUrlFormProps) {
  return (
    <div className="form">
      <div className="field">
        <label htmlFor="jobUrl">Job posting URL</label>
        <input
          id="jobUrl"
          onChange={(event) => onChange(event.target.value)}
          placeholder="https://jobs.lever.co/company/role"
          value={url}
        />
        <p className="helper-text">
          First pass supports Greenhouse, Lever, Ashby, and generic HTML job pages.
        </p>
        {validationError ? <p className="field-error">{validationError}</p> : null}
      </div>

      <div>
        <button className="button" disabled={isSaving} onClick={onSubmit} type="button">
          {isSaving ? "Ingesting..." : "Ingest Job"}
        </button>
      </div>
    </div>
  );
}
