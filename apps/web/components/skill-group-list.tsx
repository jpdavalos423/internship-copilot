type SkillGroupListProps = {
  groups: Record<string, string[]>;
  emptyMessage: string;
};

export function SkillGroupList({ groups, emptyMessage }: SkillGroupListProps) {
  const entries = Object.entries(groups);

  if (!entries.length) {
    return <p className="empty-state">{emptyMessage}</p>;
  }

  return (
    <div className="grid">
      {entries.map(([category, skills]) => (
        <div className="category-block" key={category}>
          <h4>{category}</h4>
          <div className="pill-list">
            {skills.map((skill) => (
              <span className="pill" key={`${category}-${skill}`}>
                {skill}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
