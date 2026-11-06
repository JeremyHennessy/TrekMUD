/* USS Asteria · original sculpted hero furniture (Pass 03)
 * Source-space room furnishing only. No game state, network, or camera mutation.
 * Shapes are purpose-built smooth parametric meshes, not a copied television set.
 */
'use strict';
window.AsteriaHero=Object.freeze({
  chair({x,z,rot=0,large=false},api){
    const {smoothSurface:S,box:B,cyl:C,tube:T,ellipse:E,ring:R}=api;
    const si=Math.sin(rot),co=Math.cos(rot), PI=Math.PI;
    const P=(a,y,b)=>[x+a*co-b*si,y,z+a*si+b*co];
    const bx=(a,y,b,w,h,d,color,m=0)=>{const p=P(a,y,b);B(p[0],p[1],p[2],w,h,d,color,m,rot);};
    const ln=(points,r,color,mat=4)=>T(points.map(p=>P(...p)),r,color,mat,9);
    const w=large?.54:.455, h=large?1.08:.93;
    const suede=large?0x73616b:0x7e6e7c;
    const leather=large?0xa18c96:0xa5969f;
    const shell=0x57555d, trim=0xc0ada6;
    let panels=0;
    // Broad load-bearing foot, swivelling graphite bearing and stem. All heights
    // are relative to an approximately 1.7-metre standing eye level.
    C(x,.085,z,.36,.33,.12,0x383a43,3,54);
    C(x,.156,z,.305,.285,.065,0x89868e,4,50);
    C(x,.225,z,.16,.16,.10,0x5a5660,3,36);
    C(x,.375,z,.085,.085,.28,0x777880,4,36);
    C(x,.54,z,.22,.185,.11,0x55535c,4,38);
    for(const sg of [-1,1]){
      bx(sg*.235,.186,.035,.24,.056,.12,0x56535e,3);
      bx(sg*.28,.18,-.135,.20,.037,.16,0x484851,4);
    }
    // Sculpted, double-layered molded seat pan with true transverse curvature.
    S(40,25,(u,v)=>{
      const a=2*u-1,b=2*v-1;
      const depth=b*.36-.065,side=a*w;
      const raised=.064*(1-a*a)+.018*Math.sin(Math.PI*v);
      return P(side,.713+raised-.018*a*a,depth);
    },suede,5,true);panels++;
    S(40,25,(u,v)=>{
      const a=2*u-1,b=2*v-1;
      return P(a*(w+.058),.615+.035*(1-a*a)-.022*b*b,b*.397-.052);
    },shell,3,true);panels++;
    // Rounded forward lip, rear seat join, and edge welting.
    for(const side of [-1,1]){
      ln([[side*w,.713,-.42],[side*w*.91,.742,-.29],[side*w*.94,.757,.09],[side*w*.89,.73,.29]],.018,0xbaa5a6,4);
    }
    ln([[-w*.82,.698,-.445],[-w*.40,.752,-.439],[0,.777,-.442],[w*.40,.752,-.439],[w*.82,.698,-.445]],.022,0x7c686d,5);
    // Continuously varying backrest cross-section, sweeps back toward shoulder.
    const back=(a,t,offset)=>{
      const half=w*(.78+.24*Math.sin(Math.PI*t)-.075*t);
      const rounded=1-.075*Math.pow(Math.abs(a),8);
      const y=.76+h*t;
      const camber=.105*(1-a*a);
      const localZ=.245+.255*t+.032*Math.sin(Math.PI*t)-camber+offset;
      return P(a*half*rounded,y,localZ);
    };
    // Soft seat-back upholstery, smooth fabric normals and depth separation.
    S(40,32,(u,v)=>back(2*u-1,v,-.029),leather,5,true);panels++;
    S(40,32,(u,v)=>back(2*u-1,v,.109),0x5e5762,3,false);panels++;
    // Physical sidewalls wrapping cushions around the back shell.
    for(const side of [-1,1]){
      S(5,32,(u,v)=>back(side,v,-.029+.138*u),0x6d616d,4,side===1);
      const edgeA=[],edgeB=[];
      for(let k=0;k<=32;k++){
        edgeA.push(back(side,k/32,-.036));
        edgeB.push(back(side,k/32,.110));
      }
      T(edgeA,.017,0xb59d9c,4,8);T(edgeB,.016,0x78717b,4,8);
    }
    // Subtle sewn upholstery panels, head/shoulder shaping and seams.
    for(const t of [.16,.49,.80]){
      const seam=[];for(let j=0;j<=40;j++){const a=-.80+j*.04;seam.push(back(a,t,-.039));}
      T(seam,.0046,t===.80?0x957d87:0x836d7a,4,5);
    }
    for(const a of [-.63,.63]){
      const seam=[];for(let j=0;j<=26;j++)seam.push(back(a,.10+j*.030,-.041));
      T(seam,.0045,0xb19ca3,4,5);
    }
    // Head cushion follows the curve rather than appearing as a rectangular brick.
    S(26,14,(u,v)=>{
      const a=2*u-1,b=2*v-1;
      const contour=Math.max(0,1-a*a);
      return P(a*w*.67,.80+h-.055+b*.092,.475+.055*Math.sqrt(contour)*(1-b*b));
    },suede,5,false);panels++;
    ln([[-w*.68,.80+h,.488],[0,.806+h,.533],[w*.68,.80+h,.488]],.012,trim,4);
    // Cast cantilever supports and fully padded independent armrests.
    for(const side of [-1,1]){
      ln([[side*(w+.19),.55,-.30],[side*(w+.15),.78,-.20],[side*(w+.145),.91,.15],[side*(w+.13),.90,.37]],.034,0x55515e,4);
      S(8,18,(u,v)=>{
        const a=2*u-1,b=2*v-1;
        return P(side*(w+.146)+a*.115,.940+.037*(1-a*a),-.18+v*.52);
      },suede,5,true);panels++;
      // Inset smoked touch strip and physical side controller.
      bx(side*(w+.15),.987,-.035,.139,.022,.26,0x242733,7);
      for(let k=0;k<5;k++)bx(side*(w+.15),1.003,-.125+k*.047,.066,.009,.026,[0xbba3b0,0x8eb9cf,0xddbb9a,0x98b6a9,0xc7b0bb][k],8);
      bx(side*(w+.16),.76,.24,.048,.30,.08,0x9d9093,4);
    }
    return {shape:'hero-contoured-seat',panels,smooth:true,version:3};
  },
  commandPlatform(api){
    const {smoothSurface:S,tube:T,ellipse:E,cyl:C,ring:R}=api;
    // A stepped oval moulding, not just a rectangular dais. The top layer
    // retains exactly the previous floor height and collision footprint.
    C(0,.115,1.11,1.85,1.54,.215,0x4c4954,3,88);
    S(96,5,(u,v)=>{
      const a=u*2*Math.PI;
      const r=.86+.14*v;
      return [Math.sin(a)*1.87*r,.236+.040*v,1.11+Math.cos(a)*1.545*r];
    },0x817780,4,false);
    E(0,.281,1.11,1.79,1.47,0x625f70,1,112);
    R(0,.291,1.11,1.85,1.54,.988,0xb99e90,4,112);
    T([[-1.70,.302,1.57],[-1.81,.31,1.94],[-1.67,.30,2.17]],.026,0xb7a196,4,10);
    T([[1.70,.302,1.57],[1.81,.31,1.94],[1.67,.30,2.17]],.026,0xb7a196,4,10);
    return {shape:'stepped-oval-bridge-dais',version:3};
  },
  commandPylons(api){
    const {smoothSurface:S,box:B,tube:T,surface:display}=api;
    for(const side of [-1,1]){
      const x=side*1.27,z=.58,rotation=side*.24;
      const co=Math.cos(rotation),si=Math.sin(rotation);
      const P=(a,y,b)=>[x+a*co-b*si,y,z+a*si+b*co];
      // Continuous flared cast housings with taper and an integral flying brow.
      S(20,18,(u,v)=>{
        const a=2*u-1,b=2*v-1;
        const bulge=(1-v)*.18;
        return P(a*(.32+bulge),.25+v*.84,b*(.32+.09*(1-v)));
      },0xaca5a4,2,true);
      S(20,12,(u,v)=>P((u-.5)*.73,1.105+Math.sin(v*Math.PI)*.04,(v-.5)*.81),0x34333c,7,false);
      const a=P(0,1.105,-.065);display(a[0],1.165,a[2],.64,.60,rotation,0xffffff,side<0?3:5,.020);
      const rim=[];for(let k=0;k<=22;k++)rim.push(P(-.33+k*.03,1.126,-.46));
      T(rim,.015,0x887b81,4,8);
      const trim=P(0,.46,.24);B(trim[0],trim[1],trim[2],.55,.070,.13,0x6c666e,4,rotation);
    }
    return {shape:'cast-command-pylons',count:2};
  },
  flightIsland(api){
    const {smoothSurface:S,box:B,tube:T,plane}=api;
    const N=52,z=x=>-3.24+.24*Math.pow(x/2.45,2);
    // One manufactured pressure-formed shell; front lower face, swept knee
    // recess and a floated armature carrying smoked touchglass screens.
    S(N,8,(u,v)=>{
      const x=(u-.5)*5.34,zz=z(x);
      const rise=.24+v*.84;
      return [x,rise,zz+.52-.10*v+.020*Math.cos(x)];
    },0xa9a2a0,2,false);
    S(N,12,(u,v)=>{
      const x=(u-.5)*5.34,zz=z(x);
      const depth=.46-1.00*v;
      const crown=.025*Math.sin(v*Math.PI)+.02*(1-Math.pow(x/2.67,2));
      return [x,1.04+.11*v+crown,zz+depth];
    },0x252730,7,true);
    S(N,7,(u,v)=>{
      const x=(u-.5)*5.34,zz=z(x);
      return [x,.245+v*.91,zz-.55];
    },0x858089,3,false);
    const lip=[],bezel=[],base=[],light=[];
    for(let i=0;i<=N;i++){
      const x=-2.67+i*5.34/N,zz=z(x);
      lip.push([x,1.19,zz-.53]);
      bezel.push([x,1.06,zz+.46]);
      base.push([x,.28,zz+.51]);
      light.push([x,.36,zz+.525]);
    }
    T(lip,.019,0xb1aaa9,4,10);
    T(bezel,.025,0x64616d,4,8);
    T(base,.026,0x51545e,4,10);
    T(light,.007,0xc2c2bd,8,7);
    for(const side of [-1,1]){
      const x=side*2.67,zz=z(x);
      plane([x,.25,zz+.51],[x,1.065,zz+.45],[x,1.17,zz-.55],[x,.24,zz-.55],0x8f898d,3);
      B(x,.31,zz+.19,.15,.08,.59,0x595963,4);
    }
    // Original instrument UVs and click-free movement remain in index.html.
    return {shape:'one-piece-swept-flight-desk',segments:N,version:3};
  },
  ceilingFixtures(api){
    const {box:B,tube:T,cyl:C}=api;
    // Low-glare cinema set practicals: broad diffusers nested in shadowed
    // housings, not perimeter neon and not isolated luminous tiles.
    const positions=[[-4.65,-2.9],[4.65,-2.9],[-4.70,1.20],[4.70,1.20],[-3.0,4.2],[3.0,4.2]];
    for(const [x,z] of positions){
      B(x,3.83,z,.98,.08,.46,0x4c4b52,3);
      B(x,3.798,z,.78,.016,.32,0xc0c5c3,8);
      for(const side of [-1,1])B(x+side*.46,3.806,z,.043,.017,.41,0x7a777a,4);
    }
    for(let s of [-1,1]){
      const pts=[];for(let i=0;i<=24;i++){
        const z=-3.95+i*.24,x=s*(4.85+.08*Math.sin(i*Math.PI/24));pts.push([x,3.73,z]);
      }
      T(pts,.019,0x948e92,4,9);
    }
    return {fixtures:positions.length,version:3};
  }
});
