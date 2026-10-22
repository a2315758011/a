const fs=require('fs'),path=require('path');
const dir='C:/Users/ide0007/Desktop/deliverable/AI小游戏实战营/AI小游戏制作工程文件/直播炮塔守城/自动化测试';
const vars={
  'qa_formal_fast_combat_20261022.py':'port',
  'qa_formal_full_game_e2e_20261022.py':'port',
  'qa_formal_liveplay_20261022.py':'port',
  'qa_formal_platform_socket_fallback_20261022.py':'port',
  'qa_formal_shop_20261022.py':'port',
  'qa_formal_shop_effects_20261022.py':'p',
  'qa_formal_shop_persistence_20261022.py':'port'
};
const out=[];
for(const [name,v] of Object.entries(vars)){
  const pth=path.join(dir,name);
  let s=fs.readFileSync(pth,'utf8');
  const re=/proc=subprocess\.Popen\(\[str\(EDGE\),[\s\S]*?\],stdout=subprocess\.DEVNULL,stderr=subprocess\.DEVNULL\)/m;
  if(!re.test(s)) throw new Error('spawn block missing '+name);
  const replacement='subprocess.run(["node",str(ROOT/"自动化测试"/"edge_cdp_launcher_20261022.js"),str('+v+'),profile],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)\n proc=None';
  s=s.replace(re,replacement);
  fs.writeFileSync(pth,s,'utf8');
  out.push({name,launcher:s.includes('edge_cdp_launcher_20261022.js')});
}
console.log(JSON.stringify(out,null,2));
