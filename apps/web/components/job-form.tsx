type JobFormState = {
  company_name: string;
  title: string;
  location: string;
  raw_text: string;
};

type JobFormProps = {
  form: JobFormState;
  isSaving: boolean;
  validationErrors: Partial<Record<keyof JobFormState, string>>;
  onChange: (value: JobFormState) => void;
  onSubmit: () => void;
};

export function JobForm({ form, isSaving, validationErrors, onChange, onSubmit }: JobFormProps) {
  function updateField<Key extends keyof JobFormState>(key: Key, value: JobFormState[Key]) {
    onChange({
      ...form,
      [key]: value,
    });
  }

  return (
    <div className="form">
      <div className="form__row">
        <div className="field">
          <label htmlFor="companyName">Company</label>
          <input
            id="companyName"
            onChange={(event) => updateField("company_name", event.target.value)}
            placeholder="Astranis"
            value={form.company_name}
          />
          {validationErrors.company_name ? <p className="field-error">{validationErrors.company_name}</p> : null}
        </div>
        <div className="field">
          <label htmlFor="jobTitle">Title</label>
          <input
            id="jobTitle"
            onChange={(event) => updateField("title", event.target.value)}
            placeholder="Backend Software Engineer Intern"
            value={form.title}
          />
          {validationErrors.title ? <p className="field-error">{validationErrors.title}</p> : null}
        </div>
      </div>

      <div className="field">
        <label htmlFor="location">Location</label>
        <input
          id="location"
          onChange={(event) => updateField("location", event.target.value)}
          placeholder="San Francisco, CA"
          value={form.location}
        />
        <p className="helper-text">Location is optional for Phase 0, but helpful for context.</p>
      </div>

      <div className="field">
        <label htmlFor="rawText">Raw job text</label>
        <textarea
          id="rawText"
          onChange={(event) => updateField("raw_text", event.target.value)}
          placeholder="Paste the full job description here..."
          value={form.raw_text}
        />
        <p className="helper-text">Raw job text is required so the deterministic parser can extract required and preferred skills.</p>
        {validationErrors.raw_text ? <p className="field-error">{validationErrors.raw_text}</p> : null}
      </div>

      <div>
        <button className="button" disabled={isSaving} onClick={onSubmit} type="button">
          {isSaving ? "Saving..." : "Create Job"}
        </button>
      </div>
    </div>
  );
}
