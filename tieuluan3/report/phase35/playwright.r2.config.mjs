import {defineConfig} from '../../apps/web/node_modules/@playwright/test/index.mjs';
import base from './playwright.config.mjs';
import {fileURLToPath} from 'node:url';
const prefix=fileURLToPath(new URL('../../artifacts/manifests/phase35/ui-r2',import.meta.url));
export default defineConfig({...base, outputDir:prefix+'-artifacts',reporter:[['line'],['junit',{outputFile:prefix+'.xml'}],['json',{outputFile:prefix+'.json'}]]});
