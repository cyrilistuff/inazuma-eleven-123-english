#!/usr/bin/env python3
"""Build the IE1 pachanga/match-chain text and team-name replacement files.

The match scripts use the same SSD text table as the Royal match patch.  This
tool deliberately limits itself to the small 9420xxxx pachanga/chain events;
the 9400xxxx story matches remain byte-for-byte original except for the
already reviewed 94001500 Royal event.  Team names are fixed 32-byte fields at
the start of each 320-byte ``team.pkb`` record, so replacing them never moves
the roster data that follows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "tools"))
from fa_unpack import FaArchive
from lz10 import compress, decompress
from pkb_unpack import parse_index
import ssd_records as S
import reinsert as R
from dialogue_typography import encode_fullwidth
from dialogue_lock import approved_layout
from build_ie1_probe import layout

EVENT_MIN = 94200000
EVENT_MAX = 94300000
ROYAL_EVENT = 94001500
MCH = "inazuma1/data_iz/script/mch."
ROYAL_MAPPING = ROOT / "translation" / "ie1" / "match_94001500.json"


# These are the short, one-off opening lines used by the optional school-club
# pachangas.  The chain events use translate_chain() below for their deliberately
# repetitive commentary.
PACHANGA_TEXT = {
    "カンタンには\\n%1F通しませんよ！": "¡No pasaréis tan fácilmente!",
    "フィギュアのためだ！\\nデータは　ぜったいにわたさない！": "¡Lo hago por mis figuras!\\n¡No pienso entregar los datos!",
    "ウラギリモノ！！": "¡¡Traidor!!",
    "%3F秘伝書は\\n%2F戦国%3F伊賀島がいただく！": "¡El cuaderno será para Shuriken!",
    "%3F相撲部でごわす！\\n%2F勝負するでごわす！": "¡Somos el club de sumo!\\n¡Nos enfrentaremos a vosotros!",
    "おいどんのツッパリ\\nうけてみるでごわす！": "¡Probad mi empujón de sumo!",
    "ちゃんこの%2F時間まで\\n%1F遊んでやるでごわすよ！": "¡Jugaremos hasta la hora del chanko!",
    "%2F勝負だ！！": "¡¡A jugar!!",
    "オレたち%2F野球%1F部と　%2F勝負しろ！\\nカンタンに%1F打ち%1F取ってやる！": "¡Enfrentaos al club de béisbol!\\n¡Os eliminaremos enseguida!",
    "おまえらなんて\\nすぐにスリーアウトチェンジさ！\\n%2F勝負しやがれ！": "¡Enseguida tendréis tres strikes!\\n¡Venga, jugad contra nosotros!",
    "%2F逆転%2F満塁ホームラン！\\nおまえらにも\\nその%2F快感を%1F教えてやるよ！": "¡Un grand slam para remontar!\\n¡Os enseñaré lo que se siente!",
    "%2F試合%2F開始！！": "¡¡Empieza el partido!!",
    "%1F勝てるかな！": "¡A ver si podéis ganar!",
    "さあ%2F時間だ！": "¡Ha llegado la hora!",
    "%1F足の%1F速さなら\\n%2F陸上%1F部のほうが%1F上だぜ？\\n%2F勝負だ！": "¡En velocidad nos gana el club de atletismo!\\n¡A ver quién vence!",
    "すっとろいヤツらめ！\\nついて%1F来れるか？\\n%2F勝負してやるよ！": "¡Qué lentos sois!\\n¿Podéis seguirnos?\\n¡Vamos a jugar!",
    "サッカーてのは\\nそんなに　のろくて%3F大丈夫なのか？\\n%2F勝負して　たしかめてやるよ！": "¿El fútbol es tan lento?\\n¡Lo comprobaremos jugando!",
    "%1F始めようか！": "¡Empezamos!",
    "いくよ！": "¡Allá vamos!",
    "がんばるぜ！": "¡Me esforzaré!",
    "%1F足でボールを%1F扱うなんて　%2F下品だな。\\nテニスの%1F方が%2F上品だよ。\\nちょっと%2F勝負してよ。": "¡Qué vulgar es tocar el balón con los pies!\\nEl tenis es más elegante.\\n¡Echamos un partido!",
    "こんな%1F大きなボールじゃ\\nラケットがもたないよ。\\n%2F仕方ない　そっちのルールで%2F勝負だ！": "¡Este balón es demasiado grande para una raqueta!\\nJugaremos con vuestras reglas.",
    "%2F絶対に%1F勝つよ！": "¡Ganaremos sin falta!",
    "サッカーバトル%2F開始だ！": "¡Empieza la pachanga!",
    "さあ　%1F楽しもう！": "¡A disfrutar!",
    "オレたち　サイクリング%1F部を\\nナメるなよ！？": "¡No subestiméis al club de ciclismo!",
    "オレたち　サイクリング%1F部を\\nナメるなよ！？\\nさあ　%2F勝負だ！！": "¡No subestiméis al club de ciclismo!\\n¡¡A jugar!!",
    "%1F足の%1F力はこっちが%1F上だってこと\\n%1F思い%1F知らせてやるよ！": "¡Os demostraremos que nuestras piernas son más fuertes!",
    "おまえら%2F相手に\\nオレのバイクは%1F使えねえ。\\nサッカーで%2F勝負してやるよ！": "No puedo usar mi bici contra vosotros.\\n¡Nos enfrentaremos jugando al fútbol!",
    "キック！　オーフ！！": "¡Kick-off! ¡Vamos!",
    "オレたち%2F柔道%1F部と　%2F勝負だ！": "¡El club de judo os desafía!",
    "あんたら%2F受身はとれるのかい？\\nケガしちまっても%1F知らないぜ！": "¿Sabéis hacer una caída de judo?\\n¡No respondemos de las lesiones!",
    "まいったするなら　%1F早いうちにな！\\nいざ　%2F勝負！": "¡Rendíos mientras podáis!\\n¡A luchar!",
    "%1F負けないよ！！": "¡¡No perderemos!!",
    "めーん！　どぅ！　こてーー！": "¡Men! ¡Do! ¡Kote!",
    "ぷはーっ\\n%2F防具をはずしたらスッキリしたな！\\n%1F行くぜ　%2F勝負だ！": "¡Uf!\\n¡Qué alivio quitarse la armadura!\\n¡Vamos a jugar!",
    "%2F真剣%2F勝負ってものを%1F教えてやろう！\\n%1F行くぞ！": "¡Os enseñaremos lo que es un duelo de verdad!\\n¡Vamos!",
    "ハットトリック？\\nこっちは　１%1F発で３%1F点とれんだよ！！\\n%2F勝負しやがれ！": "¿Un hat-trick?\\n¡Nosotros marcamos tres goles de un tiro!\\n¡Enfrentaos a nosotros!",
    "おいおい　オレたちに\\nさわるんじゃねえぞ！\\nバスケじゃ%2F反則なんだからな！": "¡Eh, no nos toquéis!\\n¡En baloncesto eso es falta!",
    "こんなでかいゴールなら\\nバカでも%1F入るっての！\\nさっさとかかって%1F来いよ！": "¡Con una portería tan grande marca cualquiera!\\n¡Venid de una vez!",
    "オレたち%2F水泳%1F部と　%2F勝負だ！\\nおまえらとは%2F体力がちがう！\\nカクゴしな！": "¡El club de natación os desafía!\\n¡Tenemos mucha más resistencia!\\n¡Preparaos!",
    "%1F泳ぎできたえた%2F体力をみせてやる！\\n%1F行くぜ　%2F勝負だ！": "¡Os enseñaremos la resistencia que da la natación!\\n¡Vamos a jugar!",
    "サッカーボールは%1F水に%1F浮く…\\nしかし　おまえらはどうかな？\\n%2F勝負だ！": "El balón flota en el agua...\\n¿Y vosotros?\\n¡A jugar!",
    "オレたち%2F漫研と　%2F勝負だ！": "¡El club de manga os desafía!",
    "ちょっと〜\\nまだペン%1F入れ%1F終わってないのにさ〜。\\nさっさと%1F終わらせてよっ！": "¡Eh!\\n¡Aún no he terminado de entintar!\\n¡Acabad de una vez!",
    "オレたち%2F囲碁%2F将棋%1F部と　%2F勝負だ！": "¡El club de go y shogi os desafía!",
    "キミたちに%2F戦略ってものを\\n%1F教えてやるよ！\\nかかって%1F来なさい！": "¡Os enseñaremos lo que es una estrategia!\\n¡Venid a por nosotros!",
    "%1F先の%1F先を%1F読む！\\nそれがあらゆるゲームの%2F基本なのさ！\\n%1F行くよっ！": "¡Hay que anticiparse al rival!\\n¡Esa es la base de cualquier juego!\\n¡Vamos!",
    "オレたち%3F新聞部と　%2F勝負だ！": "¡El club de periodismo os desafía!",
    "オレたちラグビー%1F部と　%2F勝負だ！": "¡El club de rugby os desafía!",
    "キック１%1F発で%2F逆転なんて\\nそこはラグビーみたいでいいな！\\n%2F勝負してやるよ！": "¡Remontar de una patada suena a rugby!\\n¡Nos enfrentaremos a vosotros!",
    "オレたちのが\\n%2F本当のフットボールなんだよ！\\n%1F行くぜ　%2F白黒つけてやる！": "¡Nosotros jugamos al fútbol de verdad!\\n¡Vamos a decidir quién es mejor!",
    "オレたち%3F応援団と　%2F勝負だ！": "¡El grupo de animadores os desafía!",
    "てめえら　%2F応援されるほどのモンか\\nオレたちに　%2F証明してみんかい！\\nかかって%1F来い！": "¿De verdad merecéis que os animemos?\\n¡Demostradlo!\\n¡Venid a por nosotros!",
    "オス！\\n%2F勝負させてもらうであります！": "¡Sí, señor!\\n¡Aceptamos el desafío!",
    "%1F帰っても　やることがないだろって？\\n%3F帰宅部は　それなりに　%1F忙しいんだよ！": "¿Que no hacemos nada al volver a casa?\\n¡El club de no hacer nada también está ocupado!",
    "%2F部活なんてよくやるねえ。\\nもしかしてよっぽどヒマなの？\\nまあ　かかって%1F来なよ！": "¿Cómo podéis estar en un club?\\n¿No tenéis nada mejor que hacer?\\n¡Venga, venid!",
    "%3F帰宅部だから　%2F運動ができないって\\nワケじゃないのさ…。\\n%1F見せてやるよっ！": "Ser del club de no hacer nada no significa que no sepamos movernos...\\n¡Os lo demostraré!",
    "わたしから\\n２%1F点とることができるかな？": "¿Podréis marcarme dos goles?",
    "%1F負けませんよ！　ボクだって\\n%2F先生の%2F弟子ですからね！": "¡No perderé!\\n¡Yo también soy discípulo del maestro!",
    "さあ　%2F特訓を%1F始めよう…！": "¡Empecemos el entrenamiento!",
    "%1F手%2F加減なしでいくぞ！": "¡No pienso contenerme!",
    "きたえなおしてやろう…！": "¡Os pondré en forma!",
    "おまえらの%2F全力を%1F見せてみな…！": "¡Enseñadme todo vuestro potencial!",
    "%1F悪いが　てかげんはせんぞ…。": "Lo siento, pero no me contendré...",
    "%1F手%2F加減はしないよ！！": "¡¡No voy a contenerme!!",
    "キミたちの%1F力を　%1F見せてもらおう…。": "Quiero ver de qué sois capaces...",
    "さあ　かかって%1F来なさい…！": "¡Venid a por mí!",
    "キミたちの%2F限界を\\nためさせてもらうよ…！": "¡Pondré a prueba vuestro límite!",
    "勝負だ！": "¡A jugar!",
}

# The match-chain package reuses a small set of reactions across all eight
# chain matches.  Keep the exact variants here so the text remains meaningful
# instead of falling back to a generic cheer when punctuation or a ruby marker
# differs from the opening lines above.
CHAIN_EXACT = {
    "このくらい　%2F当然さ。": "¡Esto era de esperar!",
    "よっしゃあ！": "¡Sí!",
    "この%2F試合は　もらったな。": "¡Este partido es nuestro!",
    "あまり　あまく%1F見るなよ！": "¡No nos subestiméis!",
    "よし！　この%2F調子で\\nやってやろうぜ！": "¡Bien!\\n¡Sigamos así!",
    "あんがいカンタンに\\n%1F入るもんだな！": "¡Al final es fácil marcar!",
    "まあ　こんなものだろ。": "Bueno, era de esperar.",
    "%1F次はないぞ…！": "¡No habrá próxima vez...!",
    "%1F勝つのはこちらだ。": "¡Nosotros ganaremos!",
    "どんどん　%1F来い！": "¡Venid todos!",
    "１０%1F年%1F早い！": "¡Os habéis adelantado!",
    "%1F決まったぞ？": "¿Ha entrado?",
    "ふっ…！": "¡Ja...!",
    "あまいコースだったのにな…！": "¡Era un pase fácil...!",
    "まあ　こんなものだろう。": "Bueno, era de esperar.",
    "ずいぶんあっさり%1F決まったな。": "¡Ha entrado con demasiada facilidad!",
    "まったく…\\n%1F何やってんだか…。": "En fin...\\n¿Qué estáis haciendo...?",
    "%1F運もこちらに%2F味方している。": "¡La suerte está de nuestro lado!",
    "あきれたものだ…！": "¡Qué decepción...!",
    "%1F敵さんは　%1F何をやってるんだ…。": "¿Qué están haciendo los rivales...?",
    "こんなことも　あるんだな…。": "Estas cosas pasan...",
    "すまない…。": "Lo siento...",
    "ダメだったか…。": "¿No ha funcionado...?",
    "ねらいが%1F甘かったか…！": "¡He apuntado mal...!",
    "ううーん　おしかった…。": "¡Qué pena...!",
    "%1F次はこんなものじゃ　すまない！": "¡La próxima no será tan fácil!",
    "クソッ！": "¡Maldita sea!",
    "%2F足元がくるった…！": "¡He perdido el equilibrio...!",
    "あまいっ！": "¡Muy fácil!",
    "それが　きさまらの%2F本気か？": "¿Eso es todo lo que tenéis?",
    "%1F決まらなかったか！": "¡No ha entrado!",
    "オレのミスだ…。": "Ha sido culpa mía...",
    "%1F運がよかったな…。": "Habéis tenido suerte...",
    "%2F幸運はそうは%1F続かない…。": "La suerte no dura para siempre...",
    "しくじったか！": "¡He metido la pata!",
    "%2F計算%1F違いだったか…。": "¿Me había equivocado en mis cálculos...?",
    "おかしいな…　%1F決まったと%1F思ったが。": "Qué raro... creía que había entrado.",
    "くそっ！": "¡Maldita sea!",
    "%2F今度は　こっちの%1F番だ！": "¡Ahora nos toca a nosotros!",
    "みんな！　ガンガン%1F攻めよう！": "¡Equipo! ¡Ataquemos con todo!",
    "この%2F程度で\\n%1F今のオレたちは　%1F止めれないぞ！": "¡Con esto no podréis detenernos!",
    "よし！　この%2F調子で\\n%2F最後までいこう。": "¡Bien! Sigamos así\\nhasta el final.",
    "オレたちを　あまく%1F見るな…！": "¡No nos subestiméis...!",
    "こっちも　%1F手はゆるめないぜ。": "Nosotros tampoco aflojaremos.",
    "%2F勝負は　これからだ…。": "El partido acaba de empezar...",
    "もうペースダウンか？": "¿Ya vais más despacio?",
    "よくぞ　われわれをやぶった…。": "Habéis logrado derrotarnos...",
    "%1F引き%1F分けか…！": "¿Un empate...!",
    "%2F決着を　つけそこねたか…。": "No hemos podido decidir el ganador...",
    "また　いつでも%1F来るがよい…。": "Volved cuando queráis...",
    "%1F勝ったか…。": "Hemos ganado...",
    "ここまでだな。": "Esto se acaba aquí.",
    "よし　この%2F調子だ！\\nここまできたら　%1F勝つしかないぞ！": "¡Bien, sigamos así!\\n¡Ya solo podemos ganar!",
    "それは　こっちのセリフだよ…。": "Eso mismo digo yo...",
    "そのとおり…。": "Exacto...",
    "ＰＫに%1F持ち%1F込まれるとはな…。": "No esperaba que llegáramos a los penaltis...",
    "ああ　よくがんばったじゃないか…。": "Sí, lo habéis hecho muy bien...",
    "また　%2F挑戦するがよい。": "Volved a intentarlo.",
    "くそ…　%1F後もう%2F少しだったのに…\\nこんな　こんな%1F所で…。": "Maldita sea... faltaba tan poco...\\nY aquí, justo aquí...",
    "くっ…　よくぞやぶった！": "¡Habéis conseguido derrotarnos!",
    "オレも%1F熱くなってきたよ！": "¡Yo también estoy entrando en calor!",
    "これを%1F待ってたぜ！": "¡Esto es lo que estaba esperando!",
    "やっと%2F調子が%1F出てきたよ…。": "Por fin estamos entrando en ritmo...",
    "ついてこれるかな？": "¿Podréis seguirnos?",
}


def translate_chain(src: str) -> str:
    """Translate the intentionally repetitive match-chain callouts.

    Exact entries are preferred.  The small rule set covers variants with the
    same meaning (the Japanese differs only by a ruby marker or a final
    punctuation mark) and leaves no Japanese fallback in the candidate.
    """
    if src in PACHANGA_TEXT:
        return PACHANGA_TEXT[src]
    if src in CHAIN_EXACT:
        return CHAIN_EXACT[src]
    s = src.replace("　", " ")
    if "よくぞここまで" in s:
        return "¡Habéis llegado muy lejos!\\n¡A jugar!"
    if "よっしゃー" in s and "実力" in s:
        return "¡Sí!\\n¡Esta es nuestra fuerza!"
    if "ギリギリ" in s and "勝" in s:
        return "¡Hemos ganado por los pelos!\\n¡Menudo rival!"
    if "見たか" in s:
        return "¡Lo habéis visto!"
    if "どうだ" in s:
        return "¡Qué os parece!"
    if "勝負だ" in s:
        return "¡A jugar!"
    if "勝ち" in s or "勝利" in s:
        return "¡Hemos ganado!"
    if "負け" in s:
        return "¡No pienso perder!"
    if "失敗" in s or "外" in s or "はず" in s or "しまった" in s:
        return "¡He fallado!"
    if "点" in s:
        return "¡Otro gol!"
    if "決め" in s:
        return "¡Marcaré el próximo!"
    if "楽し" in s:
        return "¡Esto se pone interesante!"
    if "強い" in s:
        return "Son fuertes...\\n¡Pero no podemos rendirnos!"
    if "油断" in s or "気合" in s:
        return "¡No bajemos la guardia!"
    if "流れ" in s:
        return "¡Aprovechemos el ritmo del partido!"
    if "チャンス" in s or "おしい" in s:
        return "¡Casi!"
    if "やる" in s:
        return "¡No está mal!"
    if "まだ" in s:
        return "¡Aún no ha terminado!"
    if "あきらめ" in s:
        return "¿Ya os rendís?"
    if "おそい" in s:
        return "¡Demasiado lentos!"
    if "バーニング" in s:
        return "¡Estamos que ardemos!"
    if "力" in s:
        return "¡Os enseñaremos nuestra fuerza!"
    return "¡Vamos, equipo!"


TEAM_EXACT = {
    "雷門": "Raimon", "帝国": "Royal Academy", "尾刈斗": "Occult",
    # Official European names confirmed in the Spanish NDS dialogue: Brain,
    # Farm and Inazuma Kids FC. Kasamino follows the reviewed story dialogue.
    "野生": "Wild", "御影専農": "Brain", "秋葉名戸": "Otaku",
    "戦国伊賀島": "Shuriken", "千羽山": "Farm", "木戸川": "Kirkwood",
    "世宇子": "Zeus", "稲妻ＫＦＣ": "Inazuma Kids FC", "傘美野": "Kasamino",
    "一番街": "Calle Mayor", "ＯＢズ": "Veteranos", "相撲部": "Club de sumo",
    "占い": "Adivinos", "コンビニ": "Tienda", "運動部": "Club deportivo",
    "野生中はぐれ": "Rezagados de Wild", "ラグビー部": "Club de rugby",
    "不良": "Gamberros", "サッカー部": "Club de fútbol",
    "帝国 (練習試合用)": "Royal (amistoso)", "うらゼウス": "Zeus oscuro",
    "ナゾの黒服": "Hombres de negro", "スラムの番人": "Guardianes del barrio",
    "秋葉名戸のオタク": "Otakus de Otaku", "戦国の忍び": "Ninjas de Shuriken",
    "ガリガリ相撲部": "Sumo esquelético", "ぽっちゃり相撲部": "Sumo regordete",
    "ぷっくり相撲部": "Sumo rechoncho", "どすこい相撲部": "Sumo doskoi",
    "よこづな相撲部": "Sumo yokozuna", "へたっぴ野球部": "Béisbol torpe",
    "しろうと野球部": "Béisbol amateur", "ほけつ野球部": "Béisbol suplente",
    "野球部レギュラー": "Titulares de béisbol", "アイドル野球部": "Béisbol de idols",
    "のろま陸上部": "Atletismo lento", "スキップ陸上部": "Atletismo saltarín",
    "かけあし陸上部": "Atletismo corredor", "しゅんそく陸上部": "Atletismo veloz",
    "マッハ陸上部": "Atletismo supersónico", "からぶりテニス部": "Tenis de raquetas al aire",
    "ノーコンテニス部": "Tenis sin control", "しゃにむにテニス部": "Tenis a tope",
    "スマッシュテニス部": "Tenis demoledor", "テニス部プリンス": "Príncipes del tenis",
    "ふらふらサイクル部": "Ciclismo tambaleante", "のりたてサイクル部": "Ciclismo novato",
    "ルンルンサイクル部": "Ciclismo alegre", "かるわざサイクル部": "Ciclismo acrobático",
    "ウイリーサイクル部": "Ciclismo en caballito", "なきむし柔道部": "Judo llorón",
    "なんちゃって柔道部": "Judo de mentira", "がむしゃら柔道部": "Judo incansable",
    "バツグン柔道部": "Judo excelente", "黒おび柔道部": "Judo de cinturón negro",
    "おこちゃま剣道部": "Kendo infantil", "ヘタレ剣道部": "Kendo cobarde",
    "ちゃんばら剣道部": "Kendo de espadachines", "たつじん剣道部": "Kendo experto",
    "サムライ剣道部": "Kendo samurái", "ちびっこバスケ部": "Baloncesto infantil",
    "じしょうバスケ部": "Baloncesto presumido", "フンフンバスケ部": "Baloncesto resoplón",
    "ダンクバスケ部": "Baloncesto de mates", "スターバスケ部": "Estrellas del baloncesto",
    "カナヅチ水泳部": "Nadadores de secano", "いぬかき水泳部": "Nadadores perrito",
    "バタあし水泳部": "Nadadores de patada", "スイマー水泳部": "Nadadores expertos",
    "トビウオ水泳部": "Nadadores pez volador", "らくがき漫研部": "Manga de garabatos",
    "おえかき漫研部": "Manga de dibujantes", "にがおえ漫研部": "Manga de retratos",
    "どうじん漫研部": "Manga de aficionados", "うれっこ漫研部": "Manga de famosos",
    "さぼり囲碁部": "Go perezoso", "おぼえたて囲碁部": "Go principiante",
    "ホビー囲碁部": "Go de hobby", "きらめき囲碁部": "Go brillante", "めいじん囲碁部": "Maestros del go",
    "いねむり新聞部": "Periodismo dormido", "かけだし新聞部": "Periodismo novato",
    "はりきり新聞部": "Periodismo entusiasta", "たっぴつ新聞部": "Periodismo de pluma ágil",
    "ベテラン新聞部": "Periodismo veterano", "ダメダメラグビー部": "Rugby patoso",
    "はんぱラグビー部": "Rugby mediocre", "かいりきラグビー部": "Rugby poderoso",
    "トライラグビー部": "Rugby de ensayos", "パワフルラグビー部": "Rugby potente",
    "よわむし応援団": "Animadores blandengues", "よせあつめ応援団": "Animadores reunidos",
    "イケイケ応援団": "Animadores cañeros", "はりきり応援団": "Animadores entusiastas",
    "オッス！応援団！": "¡Animadores, sí señor!", "ぼんやり帰宅部": "Club de casa despistado",
    "きまぐれ帰宅部": "Club de casa caprichoso", "さわやか帰宅部": "Club de no hacer nada alegre",
    "おしゃれ帰宅部": "Club de no hacer nada moderno", "モテモテ帰宅部": "Club de no hacer nada popular",
    "イナビカリアローズ": "Inazuma Arrows", "イナビカリシールズ": "Inazuma Shields",
    "イナビカリスピアズ": "Inazuma Spears", "イナビカリガンズ": "Inazuma Guns",
    "イナビカリボムズ": "Inazuma Bombs", "イナビカリロケッツ": "Inazuma Rockets",
    "イナビカリジェッツ": "Inazuma Jets", "イナビカリタンクス": "Inazuma Tanks",
    "レイトンチーム": "Equipo Layton", "イナビカリベイブス": "Inazuma Babes",
    "イナビカリキッズ": "Inazuma Kids", "イナビカリボーイズ": "Inazuma Boys",
    "イナビカリヤングス": "Inazuma Youngs", "イナビカリブラッズ": "Inazuma Brads",
    "イナビカリワイルズ": "Inazuma Wilds", "イナビカリダークス": "Inazuma Darks",
    "イナビカリナイツ": "Inazuma Knights", "イナビカリキングス": "Inazuma Kings",
    "イナビカリデビルス": "Inazuma Devils", "イナビカリダミーチーム": "Equipo de prueba Inazuma",
}


def translate_team(name: str) -> str:
    if name in TEAM_EXACT:
        return TEAM_EXACT[name]
    m = re.fullmatch(r"(.+チーム)０([６７８])", name)
    if m:
        base = {"相撲部チーム": "Equipo de sumo", "野球部チーム": "Equipo de béisbol",
                "陸上部チーム": "Equipo de atletismo", "テニス部チーム": "Equipo de tenis",
                "サイクルチーム": "Equipo de ciclismo", "柔道部チーム": "Equipo de judo",
                "剣道部チーム": "Equipo de kendo", "バスケ部チーム": "Equipo de baloncesto",
                "水泳部チーム": "Equipo de natación", "漫研チーム": "Equipo de manga",
                "囲碁将棋チーム": "Equipo de go y shogi", "新聞部チーム": "Equipo de periodismo",
                "ラグビーチーム": "Equipo de rugby", "応援団チーム": "Equipo de animadores",
                "帰宅部チーム": "Equipo de no hacer nada"}.get(m.group(1))
        if base:
            return base + " " + m.group(2)
    return "Equipo rival"


CLUBINFO_EXACT = {
    "対象外": "Fuera de categoría", "サッカー部": "Club de fútbol",
    "相撲部": "Club de sumo", "野球部": "Club de béisbol",
    "陸上部": "Club de atletismo", "テニス部": "Club de tenis",
    "サイクリング部": "Club de ciclismo", "柔道部": "Club de judo",
    "剣道部": "Club de kendo", "バスケ部": "Club de baloncesto",
    "バトミントン部": "Club de bádminton", "新体操部": "Gimnasia rítmica",
    "水泳部": "Club de natación", "漫研": "Club de manga",
    "囲碁将棋部": "Club de go y shogi", "新聞部": "Club de periodismo",
    "ラグビー部": "Club de rugby", "応援団": "Animadores",
    "写真部": "Club de fotografía", "帰宅部": "Club de no hacer nada",
}


def patch_clubinfo(arc: FaArchive):
    source = bytearray(get_bytes(arc, "inazuma1/data_iz/logic/clubinfo.dat"))
    if len(source) % 32:
        raise ValueError("clubinfo.dat is not a 32-byte record table")
    changes = []
    for rec in range(len(source) // 32):
        start = rec * 32
        raw = bytes(source[start:start + 32]).split(b"\0", 1)[0]
        name = raw.decode("shift_jis")
        translated = CLUBINFO_EXACT.get(name)
        if translated is None:
            if name.startswith("部活"):
                digits = name[2:].translate(str.maketrans("０１２３４５６７８９", "0123456789"))
                translated = f"Club {digits}"
            else:
                translated = name
        body = R.es_encode(translated, 32)
        if len(body) >= 32:
            raise ValueError(f"club info exceeds fixed field: {name!r} -> {translated!r}")
        source[start:start + 32] = body + bytes(32 - len(body))
        changes.append({"record": rec, "source": name, "text": translated})
    return bytes(source), changes


def get_bytes(arc: FaArchive, path: str) -> bytes:
    _, off, size = next(e for e in arc.entries if e[0] == path)
    return bytes(arc.d[off:off + size])


def patch_mch(arc: FaArchive):
    pkh = get_bytes(arc, MCH + "pkh")
    pkb = get_bytes(arc, MCH + "pkb")
    index = parse_index(pkh)
    mapping = json.loads(ROYAL_MAPPING.read_text(encoding="utf-8"))
    if int(mapping["event_id"]) != ROYAL_EVENT:
        raise ValueError("Royal match mapping event_id mismatch")
    royal_translations = {int(k): v for k, v in mapping["records"].items()}
    out = bytearray(); new_index = []; reports = []
    for eid, off, size in index:
        payload = pkb[off:off + size]
        if eid == ROYAL_EVENT or EVENT_MIN <= eid < EVENT_MAX:
            dec = decompress(payload)
            try:
                _, instructions, records = S.parse(dec)
            except ValueError:
                records = []
            replacements = {}
            for i, record in enumerate(records):
                if instructions.get(record.instruction) != 0x301D or record.argument != 1:
                    continue
                src = record.body.decode("shift_jis")
                if eid == ROYAL_EVENT:
                    if i not in royal_translations:
                        raise ValueError(f"Royal mapping missing visible record {i}")
                    text = royal_translations[i]
                    formatted = approved_layout(text, layout)
                    body = encode_fullwidth(formatted)
                else:
                    text = translate_chain(src)
                    # The match scripts have no furigana consumption dependency;
                    # all output is plain Spanish and obeys the same SSD limit.
                    body = R.es_encode(text, 1 << 20)
                replacements[i] = body
            if eid == ROYAL_EVENT:
                visible = {i for i, record in enumerate(records)
                           if instructions.get(record.instruction) == 0x301D and record.argument == 1}
                if visible != set(royal_translations):
                    missing = sorted(visible - set(royal_translations))
                    extra = sorted(set(royal_translations) - visible)
                    raise ValueError(f"Royal mapping mismatch: missing={missing}, extra={extra}")
            if replacements:
                changed = S.replace(dec, replacements)
                payload = compress(changed)
                assert decompress(payload) == changed
                reports.append({"event": eid, "records": len(replacements),
                                "japanese_before": len(replacements),
                                "scope": "royal" if eid == ROYAL_EVENT else "pachanga"})
        new_index.append((eid, len(out), len(payload)))
        out.extend(payload); out.extend(bytes((-len(out)) % 4))
    header = bytearray(pkh[:0x30])
    for row in new_index:
        header.extend(struct.pack("<III", *row))
    header.extend(pkh[0x30 + len(index) * 12:])
    assert len(header) == len(pkh)
    return bytes(header), bytes(out), reports


def patch_teams(arc: FaArchive):
    source = bytearray(get_bytes(arc, "inazuma1/data_iz/logic/team.pkb"))
    if len(source) % 320:
        raise ValueError("team.pkb is not a 320-byte record table")
    # Official European names from the Spanish NDS team.pkb, by 3DS record index
    # (the NDS table inserts one extra team at record 32).
    import csv
    glossary = ROOT / "translation" / "shared" / "glossary" / "equipos.csv"
    with glossary.open(encoding="utf-8", newline="") as f:
        official = {int(row["idx"]): row for row in csv.DictReader(f)}
    changes = []
    for rec in range(len(source) // 320):
        start = rec * 320
        field = bytes(source[start:start + 32])
        raw = field.split(b"\0", 1)[0]
        try:
            name = raw.decode("shift_jis")
        except UnicodeDecodeError:
            continue
        if not name:
            continue
        row = official.get(rec)
        if row and row["japones"] == name:
            translated = row["espanol_oficial"]
        else:
            translated = translate_team(name)
        body = R.es_encode(translated, 32)
        if len(body) >= 32:
            raise ValueError(f"team name exceeds fixed field: {name!r} -> {translated!r}")
        source[start:start + 32] = body + bytes(32 - len(body))
        changes.append({"record": rec, "source": name, "text": translated})
    return bytes(source), changes


def patch_team_titles(arc: FaArchive):
    source = bytearray(get_bytes(arc, "inazuma1/data_iz/logic/teamtitle.dat"))
    # The title table has 16-byte slots.  The odd slots are metadata; only
    # slots present in the reviewed glossary are touched.
    glossary = ROOT / "translation" / "shared" / "glossary" / "titulos_equipo.csv"
    rows = []
    import csv
    with glossary.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    changes = []
    for row in rows:
        idx = int(row["idx"]); source_name = row["japones"]
        start = idx * 16
        if start + 16 > len(source):
            raise ValueError("teamtitle index outside table")
        current = bytes(source[start:start + 16]).split(b"\0", 1)[0].decode("shift_jis")
        if current != source_name:
            raise ValueError(f"teamtitle source mismatch at {idx}: {current!r} != {source_name!r}")
        text = row["espanol_oficial"]
        if source_name == "伝説のイレブン":
            text = "Equipo leyenda"
        body = R.es_encode(text, 16)
        if len(body) >= 16:
            raise ValueError(f"team title exceeds fixed field: {text!r}")
        source[start:start + 16] = body + bytes(16 - len(body))
        changes.append({"slot": idx, "source": source_name, "text": text})
    return bytes(source), changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra-files", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    extra = args.extra_files.resolve()
    arc = FaArchive(str(ROOT / "work" / "shared" / "base_3ds" / "romfs" / "archive.fa"))
    pkh, pkb, mch_report = patch_mch(arc)
    team, team_report = patch_teams(arc)
    titles, title_report = patch_team_titles(arc)
    clubinfo, clubinfo_report = patch_clubinfo(arc)
    files = {
        MCH + "pkh": pkh,
        MCH + "pkb": pkb,
        "inazuma1/data_iz/logic/team.pkb": team,
        "inazuma1/data_iz/logic/teamtitle.dat": titles,
        "inazuma1/data_iz/logic/clubinfo.dat": clubinfo,
    }
    for rel, payload in files.items():
        path = extra / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    report = {
        "scope": "IE1 pachanga events 9420xxxx, match-chain events 94200251-94200258, team names, titles, and club categories",
        "mch_events": mch_report,
        "mch_archive_sha256": hashlib.sha256(pkb).hexdigest(),
        "team_names": team_report,
        "team_titles": title_report,
        "clubinfo": clubinfo_report,
        "files": {rel: hashlib.sha256(payload).hexdigest() for rel, payload in files.items()},
        "typography": "unchanged; dialogue_lock v20 remains enforced by build_ie1_probe.py",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"mch_events": len(mch_report), "team_names": len(team_report),
                      "team_titles": len(title_report), "clubinfo": len(clubinfo_report)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
