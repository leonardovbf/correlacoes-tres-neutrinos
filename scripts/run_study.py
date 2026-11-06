#!/usr/bin/env python3
"""Prepara e executa o estudo completo; nunca envia jobs IBM implicitamente."""
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from app.backend import audit, service, study
from app.backend.storage import RunStore


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','smoke','run','resume','analyze','hardware-plan','collect-hardware','prepare-fast','revalidate','prepare-recovery','prepare-trotter-recovery','prepare-hardware-queue','queue-hardware'])
    parser.add_argument('record',nargs='?',type=Path,help='study.json para retomar ou analisar')
    parser.add_argument('--output',type=Path,default=ROOT/'results')
    parser.add_argument('--without-extension',action='store_true',help='Omitir somente a extensão N=12/16; registrar escopo')
    parser.add_argument('--next-phase',action='store_true',
                        help='Executar somente a próxima fase pendente, com análise e controles (run, resume ou smoke)')
    parser.add_argument('--backend',help='Backend físico para o protocolo T08')
    parser.add_argument('--max-depth',type=int,default=20000)
    parser.add_argument('--allow-hardware',action='store_true',help='Autoriza envios reais em queue-hardware')
    parser.add_argument('--reference-checks',type=Path,help='JSON dos 120 controles de convergência da emenda v4')
    args=parser.parse_args()
    if args.next_phase and args.command not in ('run','resume','smoke'):
        parser.error('--next-phase é permitido somente com run, resume ou smoke')
    if args.allow_hardware and args.command!='queue-hardware':
        parser.error('--allow-hardware é permitido somente com queue-hardware')
    service.store=RunStore(args.output.resolve())
    try:
        if args.command=='prepare-hardware-queue':
            if not args.record or not args.backend:
                raise ValueError('Informe study.json e --backend')
            from app.backend.hardware_queue import prepare
            print(json.dumps(prepare(args.record,args.backend,max_depth=args.max_depth,progress=lambda s:print(s,flush=True)),ensure_ascii=False,indent=2))
            return 0
        if args.command=='queue-hardware':
            if not args.record:
                raise ValueError('Informe hardware-queues/ID/queue.json')
            from app.backend.hardware_queue import enqueue
            print(json.dumps(enqueue(args.record,allow_hardware=args.allow_hardware,progress=lambda s:print(s,flush=True)),ensure_ascii=False,indent=2))
            return 0
        if args.command=='prepare-recovery':
            if not args.record:
                raise ValueError('Informe study.json do estudo interrompido')
            from app.backend.recovery import prepare
            print(json.dumps(prepare(args.record,progress=lambda s:print(s,flush=True)),ensure_ascii=False,indent=2))
            return 0
        if args.command=='prepare-trotter-recovery':
            if not args.record:
                raise ValueError('Informe study.json do estudo interrompido na T06')
            from app.backend.trotter_recovery import prepare
            print(json.dumps(prepare(args.record,checks_path=args.reference_checks,
                                     progress=lambda s:print(s,flush=True)),ensure_ascii=False,indent=2))
            return 0
        if args.command=='revalidate':
            if not args.record:
                raise ValueError('Informe study.json para revalidar os controles')
            from app.backend.revalidation import revalidate
            result=revalidate(args.record,progress=lambda s:print(s,flush=True))
            print(json.dumps(result,ensure_ascii=False,indent=2))
            return 0 if result['status']=='passed' else 2
        if args.command=='prepare-fast':
            if not args.record:
                raise ValueError('Informe study.json do estudo original, entre fases')
            from app.backend.optimization import prepare_continuation
            print(json.dumps(prepare_continuation(args.record,progress=lambda s:print(s,flush=True)),
                             ensure_ascii=False,indent=2))
            return 0
        if args.command=='hardware-plan':
            if not args.record or not args.backend:
                raise ValueError('Informe study.json e --backend')
            print(study.hardware_plan(args.record,args.backend,max_depth=args.max_depth))
            return 0
        if args.command=='collect-hardware':
            if not args.record:
                raise ValueError('Informe protocols/<id>/run.json da coleta IBM')
            print(json.dumps(study.collect_hardware(args.record),ensure_ascii=False,indent=2))
            return 0
        if args.command=='plan':
            result=study.preflight(extension=not args.without_extension)
            audit.atomic_json(service.store.root/'study_preflight.json',result)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            return 0 if result['ready'] else 1
        if args.command=='analyze':
            if not args.record:
                raise ValueError('Informe study.json')
            state=json.loads(args.record.read_text())
            if audit.environment_differences(state['environment']):
                raise ValueError('Recalcule com o snapshot original; fontes/dependências mudaram')
            if args.record.resolve().parents[2]!=service.store.root:
                raise ValueError('Use o mesmo --output do estudo')
            for phase in state['phases']:
                if not phase.get('protocol_record'):
                    continue
                p=Path(phase['protocol_record'])
                record=json.loads(p.read_text())
                if record['status']!='completed':
                    continue
                spec=study.protocol.read_protocol(p.parent/'protocol.json')
                report=study.analyze_phase(service.store.root,spec,record,smoke=state['profile']=='software-smoke',
                    repetitions=40 if state['profile']=='software-smoke' else 2000,
                    reference_overrides=phase.get('reference_overrides'))
                destination=args.record.parent/phase['name']/'analysis_recomputed.json'
                audit.atomic_json(destination,report)
                print(destination)
            return 0
        if args.command=='resume' and not args.record:
            raise ValueError('Informe study.json para a retomada')
        result=study.run_study(smoke=args.command=='smoke',extension=not args.without_extension,
            resume=args.record if args.command=='resume' else None,progress=lambda s:print(s,flush=True),
            next_phase=args.next_phase)
        print(json.dumps({'status':result['status'],'record_path':result['record_path'],
                          'next_phase':result['next_phase']},indent=2))
        return 0
    except (ValueError,OSError,study.protocol.ProtocolFailed) as exc:
        print(f'Falha: {exc}',file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
