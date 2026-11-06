const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const [stateArg,project,buildRootArg,frontArg,apiArg,kongArg,mailArg]=process.argv.slice(2);
if(!/^[a-z][a-z0-9-]{2,45}$/.test(project||''))throw Error('Invalid project name');
const state=path.resolve(stateArg),repo=path.resolve(__dirname,'..'),buildRoot=path.resolve(buildRootArg);
const front=Number(frontArg),api=Number(apiArg),kong=Number(kongArg),mail=Number(mailArg);
if([front,api,kong,mail].some(p=>!Number.isInteger(p)||p<1024||p>65535)||new Set([front,api,kong,mail]).size!==4)throw Error('Invalid ports');
fs.mkdirSync(state,{recursive:true});
const random=n=>crypto.randomBytes(n).toString('hex');
const parse=file=>Object.fromEntries(fs.readFileSync(file,'utf8').split(/\r?\n/).filter(l=>/^[A-Z_][A-Z_0-9]*=/.test(l)).map(l=>{const i=l.indexOf('=');return [l.slice(0,i),l.slice(i+1)];}));
const writeEnv=(file,data)=>fs.writeFileSync(file,Object.entries(data).map(([k,v])=>`${k}=${v}`).join('\n')+'\n');
// Docker Desktop cannot reliably bind individual files through a Windows junction.
// Keep runtime bind sources in the real ASCII state directory, outside the checkout.
const runtime=path.join(process.env.USERPROFILE,'Documents','ScamGymRuntime',project);
fs.mkdirSync(runtime,{recursive:true});
const upstream=path.join(runtime,'supabase-runtime');
fs.cpSync(path.join(repo,'dev/supabase/docker'),upstream,{recursive:true,filter:p=>path.basename(p)!=='.env'});
const sbFile=path.join(state,'supabase.env');
let sb;
if(fs.existsSync(sbFile))sb=parse(sbFile);else{
 sb=parse(path.join(repo,'dev/supabase/docker/.env.example'));
 Object.assign(sb,{POSTGRES_PASSWORD:random(24),JWT_SECRET:random(32),DASHBOARD_USERNAME:'localadmin',DASHBOARD_PASSWORD:random(24),SECRET_KEY_BASE:random(48),VAULT_ENC_KEY:random(16),PG_META_CRYPTO_KEY:random(24),REALTIME_DB_ENC_KEY:random(8),POOLER_TENANT_ID:'gameplay',POSTGRES_PORT:'5432',POSTGRES_DB:'postgres',SMTP_HOST:'mailcatcher',SMTP_PORT:'1025',SMTP_USER:'',SMTP_PASS:'',SMTP_ADMIN_EMAIL:'noreply@example.com',SMTP_SENDER_NAME:'ScamGym Local',ENABLE_PHONE_SIGNUP:'false',OPENAI_API_KEY:'',LOGFLARE_PUBLIC_ACCESS_TOKEN:random(24),LOGFLARE_PRIVATE_ACCESS_TOKEN:random(24),S3_PROTOCOL_ACCESS_KEY_ID:random(16),S3_PROTOCOL_ACCESS_KEY_SECRET:random(32)});
 const now=Math.floor(Date.now()/1000);
 for(const [key,role]of[['ANON_KEY','anon'],['SERVICE_ROLE_KEY','service_role']]){
  const data=Buffer.from(JSON.stringify({alg:'HS256',typ:'JWT'})).toString('base64url')+'.'+Buffer.from(JSON.stringify({role,iss:'supabase',iat:now,exp:now+86400*3650})).toString('base64url');
  sb[key]=data+'.'+crypto.createHmac('sha256',sb.JWT_SECRET).update(data).digest('base64url');
 }
}
Object.assign(sb,{SUPABASE_PUBLIC_URL:`http://localhost:${kong}`,API_EXTERNAL_URL:`http://localhost:${kong}`,SITE_URL:`http://localhost:${front}`});writeEnv(sbFile,sb);
const envFile=path.join(state,'app.env');
let env=fs.existsSync(envFile)?parse(envFile):{SECRET_KEY:random(32),FIRST_SUPERUSER:'admin@example.com',FIRST_SUPERUSER_PASSWORD:random(24),GOOGLE_API_KEY:''};
if(!env.GOOGLE_API_KEY&&fs.existsSync(path.join(repo,'.env'))){const existing=parse(path.join(repo,'.env'));if(existing.GOOGLE_API_KEY&&!existing.GOOGLE_API_KEY.startsWith('your-'))env.GOOGLE_API_KEY=existing.GOOGLE_API_KEY;}
Object.assign(env,{PROJECT_NAME:'ScamGym 養成版',ENVIRONMENT:'local',DOMAIN:'localhost',FRONTEND_HOST:`http://localhost:${front}`,BACKEND_CORS_ORIGINS:`http://localhost:${front},http://127.0.0.1:${front}`,POSTGRES_SERVER:'supavisor',POSTGRES_PORT:'5432',POSTGRES_USER:'postgres.gameplay',POSTGRES_DB:'postgres',POSTGRES_PASSWORD:sb.POSTGRES_PASSWORD,UV_PROJECT_ENVIRONMENT:'/app/.venv',SMTP_HOST:'mailcatcher',SMTP_PORT:'1025',SMTP_TLS:'false',EMAILS_FROM_EMAIL:'noreply@example.com',SCENARIO_MODEL:env.SCENARIO_MODEL??'google:gemini-3.5-flash',SCENARIO_FALLBACK_MODELS:env.SCENARIO_FALLBACK_MODELS??'google:gemini-3.5-flash-lite,google:gemini-3.1-flash-lite'});writeEnv(envFile,env);
const cfg=JSON.parse(cp.execFileSync('docker',['compose','--project-directory',upstream,'--env-file',sbFile,'-p',project,'-f',path.join(upstream,'docker-compose.yml'),'config','--format','json'],{encoding:'utf8',maxBuffer:8*1024*1024,stdio:['pipe','pipe','pipe']}));
cfg.name=project;delete cfg.networks.default.name;
cfg.volumes={'db-config':{},'deno-cache':{},'gameplay-pgdata-v3':{},'gameplay-storage':{}};
for(const service of Object.values(cfg.services)){
 delete service.container_name;delete service.ports;
 if(service.volumes)service.volumes=service.volumes.map(v=>v.target==='/var/lib/postgresql/data'?{type:'volume',source:'gameplay-pgdata-v3',target:v.target}:v.target==='/var/lib/storage'?{type:'volume',source:'gameplay-storage',target:v.target}:v);
}
cfg.services.kong.ports=[{target:8000,published:String(kong),host_ip:'127.0.0.1',protocol:'tcp'}];cfg.services.kong.environment.KONG_NGINX_WORKER_PROCESSES='1';
cfg.services.mailcatcher={image:'schickling/mailcatcher',ports:[`127.0.0.1:${mail}:1080`]};
const image=project+'-backend:gameplay-v1.1',frontImage=project+'-frontend:gameplay-v1.1';
const log={driver:'json-file',options:{'max-size':'10m','max-file':'3'}};
const skillRoot=path.join(runtime,'skills');fs.cpSync(path.join(repo,'backend/skills'),skillRoot,{recursive:true});
const appVolumes=[{type:'bind',source:skillRoot,target:'/app/backend/skills',read_only:true}];
cfg.services.prestart={image,build:{context:buildRoot,dockerfile:'backend/Dockerfile'},env_file:[envFile],environment:{UV_PROJECT_ENVIRONMENT:'/app/.venv'},command:['uv','run','--no-sync','bash','scripts/prestart.sh'],volumes:appVolumes,depends_on:{supavisor:{condition:'service_healthy'}}};
// One local worker keeps independent full Supabase stacks within desktop memory.
// Application routes, PostgreSQL locking and production deployment remain unchanged.
cfg.services.backend={image,restart:'unless-stopped',env_file:[envFile],volumes:appVolumes,ports:[`127.0.0.1:${api}:8000`],command:['uv','run','--no-sync','fastapi','run','--workers','1','app/main.py'],depends_on:{prestart:{condition:'service_completed_successfully'}},healthcheck:{test:['CMD','curl','-fsS','http://127.0.0.1:8000/api/v1/utils/health-check/'],interval:'5s',timeout:'5s',retries:30,start_period:'40s'},logging:log};
cfg.services['season-worker']={image,restart:'unless-stopped',env_file:[envFile],command:['uv','run','--no-sync','python','-m','app.progression.close_seasons','--watch','--interval','10'],depends_on:{prestart:{condition:'service_completed_successfully'}},logging:log};
cfg.services.frontend={image:frontImage,build:{context:buildRoot,dockerfile:'frontend/Dockerfile',args:{VITE_API_URL:`http://localhost:${api}`,NODE_ENV:'production'}},restart:'unless-stopped',ports:[`127.0.0.1:${front}:80`],depends_on:{backend:{condition:'service_healthy'}},healthcheck:{test:['CMD','curl','-fsS','http://127.0.0.1/'],interval:'5s',timeout:'5s',retries:15},logging:log};
const sourceMount={type:'bind',source:repo,target:'/workspace',read_only:true},artifactMount={type:'bind',source:path.join(runtime,'artifacts'),target:'/artifacts'};fs.mkdirSync(artifactMount.source,{recursive:true});
cfg.services['backend-tests']={profiles:['tests'],image,env_file:[envFile],environment:{POSTGRES_DB:'scamgym_test',GOOGLE_API_KEY:'',UV_PROJECT_ENVIRONMENT:'/app/.venv'},working_dir:'/workspace/backend',volumes:[sourceMount,artifactMount],depends_on:{supavisor:{condition:'service_healthy'}}};
const frontendMount={type:'bind',source:path.join(repo,'frontend'),target:'/review/frontend',read_only:true};
cfg.services['frontend-tests']={profiles:['tests'],image:project+'-frontend-tests:gameplay-v1.1',build:{context:buildRoot,dockerfile:'frontend/Dockerfile',target:'test-stage'},working_dir:'/app/frontend',volumes:[frontendMount,artifactMount]};
cfg.services.playwright={profiles:['tests'],image:project+'-playwright:gameplay-v1.1',build:{context:buildRoot,dockerfile:'frontend/Dockerfile.playwright',args:{VITE_API_URL:'http://backend:8000'}},working_dir:'/app/frontend',env_file:[envFile],environment:{VITE_API_URL:'http://backend:8000',MAILCATCHER_HOST:'http://mailcatcher:1080',CI:'true'},ipc:'host',volumes:[frontendMount,artifactMount]};
fs.writeFileSync(path.join(state,'compose.json'),JSON.stringify(cfg,null,2));
const inputHash=crypto.createHash('sha256');
const ignoredBuildFolders=new Set(['node_modules','dist','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','test-results','playwright-report','blob-report','.auth']);
function hashInput(relative){const absolute=path.join(repo,relative);if(!fs.existsSync(absolute))return;const stat=fs.lstatSync(absolute);if(stat.isDirectory()){for(const name of fs.readdirSync(absolute).sort())if(!ignoredBuildFolders.has(name))hashInput(path.join(relative,name));}else if(stat.isFile()&&!/^\.env(?:\.|$)/.test(path.basename(relative))&&!relative.endsWith('.pyc')){inputHash.update(relative.split(path.sep).join('/'));inputHash.update('\0');inputHash.update(fs.readFileSync(absolute));}}
for(const relative of ['.dockerignore','package.json','bun.lock','pyproject.toml','uv.lock','backend/Dockerfile','backend/pyproject.toml','backend/alembic.ini','backend/app','backend/scripts','frontend'])hashInput(relative);
inputHash.update(`api=http://localhost:${api}`);
const sourceFingerprint=inputHash.digest('hex');
fs.writeFileSync(path.join(state,'environment.json'),JSON.stringify({version:'gameplay-v1.1',project,repo,buildRoot,state,runtime,artifacts:artifactMount.source,website:`http://localhost:${front}`,api:`http://localhost:${api}`,supabase:`http://localhost:${kong}`,mail:`http://localhost:${mail}`,database:'Supabase PostgreSQL via Supavisor:5432',sqlite:false,keyConfigured:!!env.GOOGLE_API_KEY,sourceFingerprint},null,2));
console.log(JSON.stringify({project,state,website:`http://localhost:${front}`,keyConfigured:!!env.GOOGLE_API_KEY}));
