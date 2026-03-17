/**
 * MiniMax Skills plugin for OpenCode.ai
 *
 * Registers the skills directory and injects bootstrap context via system prompt transform.
 */

import path from 'path';
import fs from 'fs';
import os from 'os';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const MiniMaxSkillsPlugin = async () => {
  const homeDir = os.homedir();
  const skillsDir = path.resolve(__dirname, '../../skills');
  const envConfigDir = process.env.OPENCODE_CONFIG_DIR
    ? path.resolve(process.env.OPENCODE_CONFIG_DIR.replace(/^~/, homeDir))
    : null;
  const configDir = envConfigDir || path.join(homeDir, '.config/opencode');

  // Discover available skills by scanning the skills directory
  const getAvailableSkills = () => {
    if (!fs.existsSync(skillsDir)) return [];
    return fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory() && fs.existsSync(path.join(skillsDir, d.name, 'SKILL.md')))
      .map(d => d.name);
  };

  const getBootstrapContent = () => {
    const skills = getAvailableSkills();
    if (skills.length === 0) return null;

    const skillList = skills.map(s => `- \`${s}\``).join('\n');

    return `<IMPORTANT>
You have MiniMax Skills available.

**Available skills:**
${skillList}

**Tool Mapping for OpenCode:**
When skills reference tools you don't have, substitute OpenCode equivalents:
- \`TodoWrite\` → \`todowrite\`
- \`Task\` tool with subagents → Use OpenCode's subagent system (@mention)
- \`Skill\` tool → OpenCode's native \`skill\` tool
- \`Read\`, \`Write\`, \`Edit\`, \`Bash\` → Your native tools

**Skills location:**
MiniMax skills are in \`${configDir}/skills/minimax-skills/\`
Use OpenCode's native \`skill\` tool to list and load skills.
</IMPORTANT>`;
  };

  return {
    // Inject skills path into live config so OpenCode discovers skills
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }
    },

    // Use system prompt transform to inject bootstrap
    'experimental.chat.system.transform': async (_input, output) => {
      const bootstrap = getBootstrapContent();
      if (bootstrap) {
        (output.system ||= []).push(bootstrap);
      }
    }
  };
};
