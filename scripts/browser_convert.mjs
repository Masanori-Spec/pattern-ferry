// Actual UI file input → acknowledgment → native browser download, with no
// production-core call from the harness. These exact files feed LMMS and Mido.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import {openApp,load,exportMusic,exportReview,xpt,smf,E} from './browser_common.mjs';
await fs.mkdir(E,{recursive:true});
const app=await openApp();const {page}=app;
try{
 await page.locator('#lang-en').click();
 await load(page,path.join(E,'native-export.xpt'));
 assert.equal(await page.locator('#note-count').textContent(),'6');
 assert.equal(await page.locator('#download').isDisabled(),true);
 await page.screenshot({path:path.join(E,'browser-native-xpt-review.png'),fullPage:true});
 await exportMusic(page,'converted.mid');await exportReview(page,'export-review.json');
 await load(page,path.join(E,'converted.mid'));
 assert.equal(await page.locator('#download').isDisabled(),true);
 await page.screenshot({path:path.join(E,'browser-midi-xpt-review.png'),fullPage:true});
 await exportMusic(page,'generated.xpt');await exportReview(page,'import-review.json');
 const cases={positive:[[0,69,24,160],[96,72,24,160],[192,76,24,160]],'missing-note':[[0,69,24,160],[192,76,24,160]],'shifted-note':[[0,69,24,160],[120,72,24,160],[192,76,24,160]]};
 for(const [name,notes]of Object.entries(cases)){await load(page,xpt(notes,288),`${name}.xpt`);await exportMusic(page,`${name}.mid`);}
 const nonintegral=smf([1,144,60,100,24,128,60,0,0,255,47,0],100);
 await fs.writeFile(path.join(E,'quantization-input.mid'),nonintegral);
 await load(page,nonintegral,'quantization-input.mid');
 assert.equal(await page.locator('#download').isDisabled(),true);
 await page.locator('input[value=nearest]').check();await page.locator('#ack').check();
 await page.screenshot({path:path.join(E,'browser-quantization-review.png'),fullPage:true});
 await exportMusic(page,'quantized.xpt');await exportReview(page,'quantized-review.json');
 assert.deepEqual(app.errors,[]);assert.deepEqual(app.network,[]);
 const files={};for(const name of ['converted.mid','generated.xpt','quantized.xpt','positive.mid','missing-note.mid','shifted-note.mid'])files[name]=crypto.createHash('sha256').update(await fs.readFile(path.join(E,name))).digest('hex');
 await fs.writeFile(path.join(E,'browser-download-result.json'),JSON.stringify({status:'pass',producer:'actual offline browser UI downloads',noNetworkRequests:true,files},null,2)+'\n');
 console.log('Actual offline UI music downloads saved for native/independent verification');
}finally{await app.browser.close();}
