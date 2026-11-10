import { fileURLToPath } from 'node:url';
import { apply as registerFilesystemSkills } from '@deepseek-ai/dsh-skill-filesystem';

export const name = 'qiandao-photo-finder';
export const inject = ['skills'];

export function apply(ctx) {
  registerFilesystemSkills(ctx, {
    providerName: 'qiandao-photo-finder',
    includeDefaultRoots: false,
    bundledSkillDir: fileURLToPath(new URL('./skills/', import.meta.url)),
    watch: false,
  });
}
