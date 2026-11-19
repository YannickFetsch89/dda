-- Nachtrag events.ort_id für den Bestand (Plan docs/plan-locations-2026-11-18.md, 3.4, Deploy-Punkt 3)
-- Erzeugt am 2026-11-19 von `python -m pipeline.ort_zuordnung --sql` (nur lesend).
-- Wiederholbar: setzt nur Treffer, die vom gespeicherten Wert abweichen; schreibt nie NULL.
-- Ein zweiter Lauf des Skripts nach dem Ausführen erzeugt keine Änderung mehr.

-- Areal Böhler (areal-boehler, spielstaette): 23 Events
UPDATE public.events SET ort_id = '6730723c-3c8b-4dc9-a6a1-f22d3177f78c' WHERE id IN ('d5fc4b55-06a1-492a-aff1-81e1bf13e616', 'f5029185-ad02-4c19-823f-9e0bbe61a622', 'd6ea20a2-3b78-4838-abb4-baa957a8aa50', '4cc4ab01-c604-45d7-8804-045cc284e32f', '09fa8387-167e-4d93-86ed-2e80d367211c', 'adbcae4c-07a2-4c99-80a6-9d409b603ff1', '9ae1bd35-b6a0-4b25-95a5-65c180a8f142', 'a35adba1-db3d-45ba-831c-187498a091be', '0f2f52b5-9901-4381-b88f-7f173f343f9d', '2a3a187c-186e-445a-b033-7024f372bca7', '66623a4a-d661-4104-b47f-8a0dd6c4c5bb', '09fc2354-461f-4bb6-88d8-af2a88894ee5', 'ce946f2d-f166-4c18-8371-c8284c1d5581', 'ff5cad84-f750-49a6-aace-68912868fb31', '112a0acb-cc26-4ad3-8164-19d2579fb0ea', 'fb42c724-2c8b-4e4e-b80f-9df8df9f7311', '51789ae9-252d-4a6d-848b-c03f8de873ee', '0f6129bb-5630-49b0-a749-6fe82ea81a35', '6828e937-dd61-48ed-8114-36731f50f110', '073be575-53c6-4e4f-a17a-f213d335f5e6', 'e99f4e39-684d-4e10-9e0e-5a125c508233', '5f38b8db-f16a-481f-a688-607300a8bf0c', 'f4e2da58-daef-471d-9e46-aeb68f602cf1');
-- CASTELLO Düsseldorf (castello-duesseldorf, spielstaette): 11 Events
UPDATE public.events SET ort_id = 'a448d28a-c22b-42a2-8eee-5f8eac28666e' WHERE id IN ('e3a24fd0-8f69-4d39-89e7-81d40948d761', '46f410ce-0b8b-4710-a8c2-0ebb8bed2673', '3e75706c-241b-4d5d-be37-7131b6dc2819', '849cdd8e-fec9-4794-abbb-7137b8a2cb26', '794404e3-560c-4459-83b5-902a17f2fe79', '019e0b11-85e9-492a-8852-10c9d2ccdf47', '26591462-e6a9-49c8-9d15-a892995cfcb8', 'e1d4c1b7-a350-4e17-a56e-12f03a2a3117', '689c5015-1546-47c2-8a55-89eeada4cfe0', '5f48942e-14bc-4efe-8af6-67c445eb0619', 'ea1a081d-61ec-4a5c-a792-4b9d2f3f6422');
-- BALLABALLA (ballaballa, spielstaette): 11 Events
UPDATE public.events SET ort_id = '2d8d4971-88bf-406d-b869-b560bd80a3e2' WHERE id IN ('de9beefa-06f5-4368-9839-9d09101af0a4', 'b52f1647-b5f0-4c2a-8d67-c20944e09036', 'd60edb3a-01ec-48cc-a63e-b043dbdca3f6', 'd6f7265a-08ae-4a3f-8d43-615b9c309859', '081b4693-0b09-4281-804d-923074ae1946', '90b1220d-0ab2-4591-9248-aeaad0e674f3', 'b93402f8-34c3-4dbf-820a-d1bd4885ff96', '5589acc8-24c5-4130-92b0-f24c3d0ef3af', '9f86abfd-7d17-4650-8e74-48de2349cedd', '20a607c2-1850-4513-a16b-b741a420c632', '6449f8a6-adf2-4be3-9aba-97f82c6e3972');
-- BrauArt (brauart, spielstaette): 10 Events
UPDATE public.events SET ort_id = '7196af2b-6db7-4978-a6df-503a311ef6b6' WHERE id IN ('27450b27-f982-436e-b1a9-82dc1710d3a2', '35e40e15-1cb1-47b7-b41e-10e18431604f', 'b97f6faa-d7a9-4769-b020-16a37b1fa40f', '39cee6b4-f15f-46b3-b71d-41cd8929d46d', '98a46cbc-8dfa-4a25-8850-847955bbe1d2', 'aca9fb2f-b404-41f6-8cec-702a32068603', '29631aee-fd43-4a61-8486-97cdc6df8a4a', '6e2f13e6-83bb-4694-a827-ad73901b73be', '9e84c5f0-f559-4deb-82fe-b5a869bd6dd6', '46c5fc08-91fd-44c9-8343-76c29cabf0e5');
-- ausARTen (ausarten, spielstaette): 10 Events
UPDATE public.events SET ort_id = '375f16de-e84e-4e5c-bd33-391264922be4' WHERE id IN ('e220e16e-66be-4875-bd30-a4205327c8a7', '19147d3a-c3d0-44d9-b2b4-75383f3224be', '708967d3-fed0-43f7-b81c-9e0a98d83eaa', '17059a49-9baa-4030-b8ad-3a6a4542985e', '1fe8a295-d1a4-4493-85fc-921ec3c90afd', 'afbd439b-8017-4d77-a621-3c727820086b', '27b269ac-17a8-465f-a464-36aa84ef3a3a', '61a844fb-5a1b-483c-a257-cb30389e028c', 'ca0052e6-6562-48ad-b9e3-7bbd2cbdd453', 'e902c018-563e-40b4-8a7e-6c672ab6b0c6');
-- Viertelladen (viertelladen, spielstaette): 10 Events
UPDATE public.events SET ort_id = '0062c2a2-cd2b-476f-a792-f7942e7b44ea' WHERE id IN ('eefe20b5-80db-4d4e-b921-4ef6e7cec7a2', 'c9c24842-ce9e-4ee3-8720-78ebcf0aab46', '21b40810-4b43-4a45-a335-f9002c2efc40', '59e95b1e-b730-4dab-a302-f9dde0608dd9', '57fef4ea-14fc-4830-bfe5-35f3b4682700', 'aa3ed3b4-e2f3-4715-a218-34713461f08b', '532c8616-d8cd-4a41-9187-d2b9fb55f37d', 'eb2a2e9f-645e-4293-837f-8dee07a8dcab', '6afa3d27-5711-4135-94e1-442c3bd4ba2e', '0ea0c1af-eb96-4b6d-83cb-43f632a72c61');
-- Rheinturm Düsseldorf (rheinturm-duesseldorf, spielstaette): 9 Events
UPDATE public.events SET ort_id = '0a4edcdb-440a-46fa-8b60-7d6bea40f701' WHERE id IN ('956d43ae-c55f-4e3f-bd5a-f406a810b2ce', 'a4d59f3d-44e6-40e6-97ad-dd8e538b966a', 'e79d17c1-e040-49e8-8f37-9deea12d4a8f', 'e1f68137-81e6-47c7-9482-31d0396adde1', 'ca4d965e-9f4f-4878-bc1d-54edfbd4bed6', 'd88d5a51-a9be-4d57-94d0-84d2c2e186da', '96466cee-2086-48df-8782-6ac2894257e6', 'e35d02c9-6d9b-47b3-9a9b-8ace1236cc49', '7cd19ab2-6af1-48ed-8417-723f908cf16d');
-- Light Space Movement (light-space-movement, spielstaette): 9 Events
UPDATE public.events SET ort_id = '5dc79be0-be37-4c1a-9047-ce370b911ad5' WHERE id IN ('67491746-8e9a-41ca-a2c3-3e9e396bac6e', '67dd7586-a200-45d0-8864-6f660cb16d1e', 'bb07495b-61cc-4265-8b7a-9fa34aff06ba', '10b57b0b-6634-4574-a179-fe68705155da', 'a9002c00-6c1b-49c3-8c99-46b343c6e79d', '05979e65-007f-4b37-89d6-f835a4680d3b', 'b04a6aab-6c80-4544-b463-b798c0709985', 'b53afa3d-0a80-4a2b-b377-ae0fb57dbdae', '92fd6b58-7d78-4f77-a557-03c389403d86');
-- Classic Remise Düsseldorf (classic-remise-duesseldorf, spielstaette): 9 Events
UPDATE public.events SET ort_id = '64b2a4c5-64c3-4fa1-a0c0-cd5af5e3aaac' WHERE id IN ('b4695787-94a0-4684-886b-58b0bd01b491', '168ad904-7fbb-42dc-b951-94fab128511b', '72aba6a7-7b0e-4dba-8642-f29f08e5b524', '950ab698-12c2-4a33-a951-d944e0742578', '46e09def-9ca7-4aeb-aa6d-731e0701fa24', '6f7ed411-bbbb-4c06-b2f3-e21089892a6e', '73760947-89b3-4f4b-aa4d-1a6898fce3e7', '0f85bd6b-f47d-4c44-ad39-0bd7fce58c61', '4b7152b5-d405-4c40-8cb3-4e243892520a');
-- Erlebnisbauernhof Gertrudenhof (erlebnisbauernhof-gertrudenhof, spielstaette): 9 Events
UPDATE public.events SET ort_id = 'd277fb69-d9b7-4e14-9589-0b1b9f54a3b9' WHERE id IN ('9dab4a7c-3cfe-47b1-9963-0e64e6e9be8c', 'c721028d-b118-48e6-8cf0-d29acde04d5c', '24fd7c45-79a7-4de6-944c-1279b7916ea4', '2c6a7650-d5fe-4efc-a90e-adcf43b04ad6', '28e1c9a3-9436-4ca5-8a06-676547f0b769', '92d2b141-98e1-4b0e-94af-82e6feb643a1', '1587c31c-cacd-430d-a96b-35b0b50e676b', 'a2d04972-d475-4e44-9788-771eed40146d', '6f6bb1ca-92d2-46e6-9762-fcb1776442ce');
-- Blumengroßmarkt (blumengrossmarkt, spielstaette): 9 Events
UPDATE public.events SET ort_id = '4a5400e2-6ca0-491f-bb49-013a43fe3385' WHERE id IN ('c919067c-bea2-4768-8863-018a28073ab2', '1b298147-de11-4685-9907-59e072a2575d', 'def19a91-f658-4c67-940e-cf083e9e372a', 'f7ed0489-0050-4f23-be4c-69574f86a367', 'fcf5228d-3970-42dc-95b0-33946c36f30c', '96084cce-8144-4e0c-a190-98994670ee5d', '24ee4356-0137-48e5-848b-6bec0baec1ef', '690b9888-5aeb-47c1-9339-45696d4700cd', 'fde3bf5b-52d1-4931-a824-2aae566cbe3f');
-- Drachental Games (drachental-games, spielstaette): 9 Events
UPDATE public.events SET ort_id = '18ea1c79-9c54-4c72-8f6e-b5c48cb5018a' WHERE id IN ('e63ecc6b-3ecf-4dfa-ba86-2bbe9f968f5c', '692960ec-8f09-4168-adf6-864c2814d7d9', '0e44a10a-fcd5-4f3d-9bc6-0531cce092f6', '3a9a3705-d9d4-4cf6-8387-211982400675', '8b2e90ac-aa64-4be8-aae2-f7624f76abb9', '92cee35a-bc0c-4473-a260-7bccd068644e', 'df2d9944-35f0-48fa-a465-9dbdce4778ee', '69c54d6f-2931-412f-9ead-0ce4d4036660', 'a43e7d1e-e313-401d-b580-04cd5d4cb9ea');
-- Bilker Häzz (bilker-haezz, spielstaette): 9 Events
UPDATE public.events SET ort_id = '4916759d-468c-44c9-9cca-48c627366d6d' WHERE id IN ('ef3045f3-ca93-4c43-998d-d94cd46b3d90', 'ff8c1d3d-21f5-4e84-8849-b5d28cde2349', '3c85ebe7-a7e7-42bb-ba22-61819d40c28e', '8596863f-8210-465a-b4c5-8041a8a2dbc5', 'f0cd57e9-0bbb-45b6-b382-50bd1ac2159e', '7e068182-0872-4a9c-851f-3aae6ebe0605', 'f3422e5f-0a6c-4f24-9c31-366602212e90', '4ff59469-e6aa-4d6b-b3d9-9d63c65b7e7b', '0f1a78de-a182-4cb2-b293-6302103475a3');
-- KLONKK – StadtStrand Indoor-Location (klonkk-stadtstrand-indoor-location, spielstaette): 8 Events
UPDATE public.events SET ort_id = '9e15beee-8960-4880-9bcf-586550289425' WHERE id IN ('edcb4344-29e5-4c46-b25a-5937a4c1896d', 'bf1d0b05-1cd1-4cd5-b9a2-ce28a0d2280d', 'a84e67aa-71e6-468a-8858-f5b03d2bb594', '3ce8d628-a588-4633-a99d-cf3dd14a8c2f', 'b1156f6a-cc94-4ec5-921c-af4c60182b71', '0437604d-097a-46c6-98eb-1da33edda271', '602a68b0-913c-4383-a0f9-3f6012f9757f', '365c01e6-f123-44da-b277-194de355a9ee');
-- Sol y Luna (sol-y-luna, spielstaette): 8 Events
UPDATE public.events SET ort_id = 'f59a4d9d-da12-4fd2-ae8c-620c2fb45d78' WHERE id IN ('72354560-6afa-43d9-b94d-e49e27a69f81', 'd1e6ecac-af86-4aca-8cc1-ddc8caf5eb37', 'fa6188f2-f6fa-4f59-8be0-96728667b082', 'f74e8ad8-a379-4335-8b2c-b431da741e0e', '04419b1a-de88-4888-93eb-7a60469e4d89', '72d63d6d-40d7-4aad-b3fa-9e7140e36b69', '48b76e89-380b-4764-bd46-64e6861407ba', 'bf54d6cb-b512-479e-838a-ec59c73e8e34');
-- The Clay Company (the-clay-company, spielstaette): 8 Events
UPDATE public.events SET ort_id = 'd4cc49c0-88ec-485a-9865-1c38ed52ad65' WHERE id IN ('34e094e1-ebc4-4936-bfc5-82b7bfba174f', 'c2b9a86d-7964-4c75-9fbd-dfabe9193550', '9ccef8b6-1b26-4c19-9418-f83147bb50ea', 'b120b0a9-acc6-470d-9918-88fe089cfa0a', 'd48e45f6-bf65-4478-98e7-13283b9113a5', 'f0563126-06e5-4086-a392-21bd2bd724ce', '7d83f2af-dbf8-4c05-9fc0-7df2d5959d25', '21f413ab-9b69-430e-bfa7-212c0c14de13');
-- ES365 Art Center (es365-art-center, spielstaette): 8 Events
UPDATE public.events SET ort_id = 'ba553ad5-8cee-4db3-9ca6-898ff0743871' WHERE id IN ('09c7ceed-af4f-4499-9c2d-67e325ea2b5c', '3e7d358f-5d9c-484c-85eb-30dfa05458c4', '22ccb8df-7769-4ed0-9662-5f64a1d8e6eb', 'c44c032a-85a1-48f3-a218-2c257ee105dc', '03467327-2c8d-4ca8-a326-0a19aa2b6f0d', 'b854d504-2836-47bd-885b-d6fc9d19a59f', '4e672061-e252-4079-9f69-58706eaba0e2', 'bbd3ac20-4109-44e7-bfbb-015e5c49a5a0');
-- RheinRiff (rheinriff, spielstaette): 7 Events
UPDATE public.events SET ort_id = '8863fb05-3423-48e7-b772-18175b8c1fbe' WHERE id IN ('26dfd6bc-2304-4390-aba8-27d7dbd49757', '5b5341fe-a9df-43fb-b36d-46827094fb84', 'e2382c3f-49dd-429e-9beb-70b40a0cf09e', 'f7383e1f-8986-4693-9f0e-f4ad2d6e15c2', '0560f7ab-7c83-4a6d-8909-1730946bcf6f', '4d65964c-009e-4b61-8ef9-f0ef3a7897f0', 'bc856dcb-8e71-4c16-b028-91e7aaa60cc3');
-- Saffran's (saffran-s, spielstaette): 7 Events
UPDATE public.events SET ort_id = '9724ce51-1f04-4c33-b37a-2d47115e458c' WHERE id IN ('a41589b8-5670-470f-91b2-5aced85339aa', '17cdda61-af3d-41f6-9277-63f7fd1b4ea9', '25cf74bc-c805-49a7-9bd2-71d066eea3d8', '0cc32542-5a63-456e-bcc2-4762747b8d5f', 'f0943e17-ffc7-427c-81a8-6373a4e6f57a', 'f1466412-8144-4483-b834-b16d8c91e28c', '450c78fb-8ad3-4c41-9585-495242975b01');
-- La Paillette (la-paillette, spielstaette): 7 Events
UPDATE public.events SET ort_id = '8ebd531f-664f-4d06-b086-9c52302fd401' WHERE id IN ('41f2b818-d9e5-48dc-be27-1fe9c25c3e3d', 'e8f8839c-7a74-4f91-a3c3-e05e508a16fa', 'c15fe9f2-01f7-49e4-b705-12b37e5fcdff', '5869eabc-f7c9-4ec3-a4c1-bdbb94ec4d30', 'b298b300-9f2d-4515-a2e8-4efabf63d710', 'a45eff5d-03df-4587-8403-2761d7342ee5', 'e562baa8-2ca7-497a-a57b-2e0764a09507');
-- hi sunny (hi-sunny, spielstaette): 7 Events
UPDATE public.events SET ort_id = 'bfe9cde0-63a0-496a-b64b-f2d8d439db3f' WHERE id IN ('2ff13999-4b48-42af-845b-ec6de180e830', '71ee7943-c5c9-4727-b7b9-81c8cf1c3da4', 'a63f33d2-908d-46d4-a2bd-8941de9d9f98', '939df309-caf6-41b3-a87d-32f9616bf1e0', '46c1b215-241f-435b-aac6-2f236beb5fa3', '2df04865-401e-48c7-abd0-eb765d7760e6', '7b5de3e8-991f-4cfb-8821-c762d655d500');
-- FLURSTÜCK (flurstueck, spielstaette): 6 Events
UPDATE public.events SET ort_id = '57f1e7e5-1111-4c0c-97b0-253d1ad31d66' WHERE id IN ('ba7595f0-2574-41ed-a068-a946bcaadcf0', '65023ba1-29a3-44cb-8326-9f0bbac52add', 'fa83fcaf-ffe0-4ae8-8361-403a16e87a13', '8f435ec5-5059-4705-85d4-3597e751357b', '7880a0fc-b3e7-46e6-b243-c34ff4302f8c', '35fbfa44-29f5-4f42-87bc-b4e01dc2a30d');
-- Globetrotter Düsseldorf (globetrotter-duesseldorf, spielstaette): 6 Events
UPDATE public.events SET ort_id = '81aaadbe-4c46-41e1-90d5-87fc0a783fcb' WHERE id IN ('e89ffacb-459f-4e77-8273-c3346095f53e', '6e820a9b-31f3-4c1c-b780-74cdbc9dcc07', 'd8b8a6f2-7cc2-4493-8991-cf615f59005b', '8592099c-2f7f-46db-b2c6-9cd3174b7364', '82995ddf-04f4-407c-88e8-da9fd873661c', '4ea74fb5-b6ab-4629-9879-a2f32c43ccb2');
-- Lakritz-Boutique (lakritz-boutique, spielstaette): 6 Events
UPDATE public.events SET ort_id = 'a084e846-44c5-4280-b7c6-0694b37bcee8' WHERE id IN ('dc0b188e-cde9-4ea5-896b-b225075690e2', 'dc21d361-ba34-4ff4-a989-278abee69882', '67536c95-dcf0-4ae9-b2d2-5b09af4a20f0', '84026c8c-f97c-4d0d-b6f5-8ec573a9edca', 'e64350f1-6ab4-46bb-86f9-9e9b6c17b171', 'e8826881-0ca7-42d4-a1b2-c2ee8ff6838d');
-- Flow, Mertensgasse 2, 40213 Düsseldorf (flow-mertensgasse-2-40213-duesseldorf, spielstaette): 5 Events
UPDATE public.events SET ort_id = '303b9d15-d73c-4f81-814e-3f063953f816' WHERE id IN ('c23b4240-72f8-4b0b-adbd-25a536214659', '7b39d178-e750-4542-acb3-5ed31e85c217', '925d2c81-20fe-48f8-a2b4-cfaa4ef99dbd', 'f57bf1ae-0e8a-4f80-a9d6-1bc892fec9fe', 'baea7af0-11a7-413d-9ecd-bcb0148f8f95');
-- Monkeyspot Düsseldorf (monkeyspot-duesseldorf, spielstaette): 5 Events
UPDATE public.events SET ort_id = '7fb93c2a-aca5-455c-9af7-a9f6a810e677' WHERE id IN ('c573b75f-d1be-4ac8-9c24-24154d24cdad', '1b3c1f62-8367-45b1-a2b3-eaa9b3b8f8a3', 'a02abd73-0f32-48ac-8d69-54075290d358', '3ec666f7-e645-41fb-81bb-b9c37c40a439', 'dcc6eeea-c792-498a-91cf-e5acfa841620');
-- Another Cotton Lab Store (another-cotton-lab-store, spielstaette): 5 Events
UPDATE public.events SET ort_id = '9cf3d98a-2d75-44b5-8bbd-45b96afda7e4' WHERE id IN ('b280505f-38eb-4b5d-b3c3-624a7dc50cd4', 'd577c0ae-ba25-497b-9107-1e782a6fcf9c', 'b9aba7bc-65d8-4601-b48d-8e26449f5f38', 'bf68ee70-41ec-4603-8cd8-0d512f4d175b', '510f4cc8-feca-43f8-932b-00f122cc3176');
-- Hockerstube (hockerstube, spielstaette): 5 Events
UPDATE public.events SET ort_id = 'c7dd47cc-b937-4386-8a36-e258ce054ca8' WHERE id IN ('e3562d38-2716-41c7-b765-2ec172381ed2', '00e7f858-1ec0-4677-a808-356ae17904b6', 'e2629cc5-96fd-456f-902d-774cfbb3e23b', '00de6d2d-e0d3-4812-98c9-60813949d940', '9f773604-7ae1-4c7d-b483-af1e586db7a0');
-- b41 (b41, spielstaette): 5 Events
UPDATE public.events SET ort_id = '576ae43e-91d5-4c30-9861-de5d63208ef3' WHERE id IN ('e6624c83-8351-4b8c-8792-9ca641ea5d56', '37ca31a9-a2e2-4075-9880-4717fb9ec3e2', '1700b3dd-fd3b-4ec2-8456-8b21569a3688', 'f5dc80cc-a5ef-493b-97a1-1891210b37fe', '3333242d-5895-4d9a-9f87-7b1cb923049c');
-- Lot jonn (lot-jonn, spielstaette): 5 Events
UPDATE public.events SET ort_id = 'd97c0fd9-343e-450e-9375-3667a328c5c3' WHERE id IN ('9a14f73a-f6dd-498c-aee9-6955abad1419', '758e282e-bdc9-4692-920f-30a3189e965e', 'e525997a-ecea-4f3c-9478-ff39c4c860cb', 'f1fc1b14-c14a-4a7f-8f14-44781d857364', 'b5a62d55-a121-4f7e-ba0c-934847ff9d72');
-- Henkel-Saal (henkel-saal, spielstaette): 4 Events
UPDATE public.events SET ort_id = '276be899-1061-4a44-8c1b-2bc26fc65a8f' WHERE id IN ('c470a326-f84e-4512-a5aa-43721b5f5a14', '47b51a53-af15-4948-81e4-adabfcaba56d', 'd4f8163b-68e5-4aab-a42c-9ecfe5088986', '26e382b2-805d-4497-afde-3968641cd986');
-- Brew Speciality Coffee & Roastery (brew-speciality-coffee-roastery, spielstaette): 4 Events
UPDATE public.events SET ort_id = '687c7b6c-2c1e-4f10-b86f-a9c71e181fdd' WHERE id IN ('86e22bb8-16ae-440e-a71f-ba2ace7a0e45', '2f6d4934-6dd5-4b7e-9809-4ca5b95a0143', 'ba89b089-2698-4e92-b7ab-40a35940988c', 'cf5f784a-4c25-4903-9912-c4b7144d21e8');
-- Maschinendorf Düsseldorf (maschinendorf-duesseldorf, spielstaette): 4 Events
UPDATE public.events SET ort_id = 'b7234ca4-1a44-4504-9761-230660962f01' WHERE id IN ('ee1703da-3f49-44df-9f5e-cfd27fa32723', 'f75713c0-e759-4c04-8bf8-d8c53815fc3b', 'e6fa6699-7593-4fb6-9549-a6945a2fc4db', '713cf5f2-62c4-472f-952e-6241b39b9c29');
-- TRIBE Hotel Düsseldorf (tribe-hotel-duesseldorf, spielstaette): 4 Events
UPDATE public.events SET ort_id = '1ec97e40-daf9-44db-a666-068920afd95c' WHERE id IN ('de4bc234-b36c-4344-b25b-20e82922b303', 'ac0c164b-91db-48e8-a5a5-b67a459835cf', '50592752-e45a-4961-8c59-02175783918a', 'd8e52961-ccc2-4776-8b69-8e1a4e85f3e9');
-- IT'S ART, BABY! (it-s-art-baby, spielstaette): 4 Events
UPDATE public.events SET ort_id = 'd7092639-31af-4db1-a012-d88e97364b00' WHERE id IN ('ca8e5f7a-2768-4492-afe6-ef033cdcb5ba', 'c98b5180-c34e-410f-a7ad-c9a329483606', '8a458794-3bdc-401d-a44f-aa6581bd5d4e', 'ffebf70e-2547-46d3-9bf6-61b8b269e6eb');
-- Plange Mühle FUENF (plange-muehle-fuenf, spielstaette): 4 Events
UPDATE public.events SET ort_id = 'adffd26f-e4bf-4237-888d-88477dc47e8a' WHERE id IN ('8b06fada-f748-4a25-85e9-8c65dafe7be5', '6644d674-2c2f-4711-a3df-90661417070a', '4ccef37a-9183-4bb2-8940-a67267562a88', 'c4344974-09b1-4770-ba80-99c9a0caccac');
-- Carlstadt - Mat Room (carlstadt-mat-room, spielstaette): 4 Events
UPDATE public.events SET ort_id = 'fbdd2937-6037-4013-bc73-084783e36624' WHERE id IN ('e2e1cb75-ce62-4bfc-b035-0f78ab56fccc', '1d58e883-8a2b-40bc-ac7d-b8907a347ef0', 'dda10b4f-6437-47a0-a7a8-a187b67c2cb7', 'c3152a5d-aeed-4fd9-b3ba-9dba7cb8f316');
-- Design Center Kronospan (design-center-kronospan, spielstaette): 4 Events
UPDATE public.events SET ort_id = 'b4ff863a-e8a0-4688-b270-ffaa0acdaad7' WHERE id IN ('d5ed90f8-68e7-4751-bcce-89342da4c7a4', '880d1945-b945-43b2-b97f-fd877fdc8e4e', '7f44aa8f-e730-411f-b5ce-881c1c5a0fc3', '116f65d6-53be-4b5c-9b8a-10afa494ed95');
-- Fünfzehnwochen Gerresheim (fuenfzehnwochen-gerresheim, spielstaette): 4 Events
UPDATE public.events SET ort_id = '251d14ee-a4cf-4608-b2f5-de0945a214ba' WHERE id IN ('470d8ae0-eb33-456e-9683-db4f9638db35', '337f45cd-b260-4d2b-9416-6d65aa1de62b', '2a992d30-5472-428a-8d3c-56dad3e57232', 'de856969-9554-4481-abca-c465a1e2e138');
-- WP8 Künstlerverein (wp8-kuenstlerverein, spielstaette): 4 Events
UPDATE public.events SET ort_id = 'dc2bc0af-f222-455d-990a-f063aa7e881b' WHERE id IN ('a2b35149-7149-4fb2-a758-3dfee3d70a2e', 'de174658-3d6a-426c-98ed-5384acdd493d', 'df5518c5-3038-43f4-9abb-f690104c5a2b', '0167495d-3fff-40e5-a8bd-24d80cb60e94');
-- Superfly Düsseldorf (superfly-duesseldorf, spielstaette): 4 Events
UPDATE public.events SET ort_id = '8fa450c7-fae0-46d4-a47b-cfa779321f28' WHERE id IN ('8e63dccc-d849-4144-b1f3-bd67ffb3d08b', '1b8ce353-5005-4b11-9d52-64419ca17363', '4db8e434-0625-401c-bea3-2d8746a78353', '1bce0d6d-85d9-411a-b0de-cacc5f12534d');
-- DJK TUSA 06 e.V (djk-tusa-06-e-v, spielstaette): 4 Events
UPDATE public.events SET ort_id = '29e09c76-2418-4035-a715-75b6cb843cce' WHERE id IN ('ce12bc71-3b7f-48f9-bf76-45148f4d32b4', '22b51d96-82a0-4947-986f-839422e15be1', 'caf491c0-25b7-4894-9505-4bd0d788e644', 'c3d66526-a208-4c1c-bb60-7ec05dc32d31');
-- Ghorban Düsseldorf (ghorban-duesseldorf, spielstaette): 4 Events
UPDATE public.events SET ort_id = 'b9b43464-7c29-4809-a878-1deb50fcae55' WHERE id IN ('36a9e91f-edd0-478a-8c36-fbf66a227fb5', '4cab8453-a12c-474d-ad3f-33756451cd9f', '79809921-1f52-43a5-a913-2a22062fcd31', '8392fa99-df31-4873-9dd9-2eda77f45144');
-- Shidokan Dojo (shidokan-dojo, spielstaette): 3 Events
UPDATE public.events SET ort_id = '2e68808f-284f-4a2c-98a5-bcece720cd53' WHERE id IN ('06485870-eb52-4030-935a-97925aad2338', '2607bbd6-65d8-402f-b906-185a7664ff9a', '1d177b4b-e265-4074-809d-9c6b5aad0d88');
-- MuSaMe (musame, spielstaette): 3 Events
UPDATE public.events SET ort_id = '5dd6bfeb-cce5-463b-a098-f2c8d0363007' WHERE id IN ('5e1628ad-e6e4-476b-a163-2d48a6aef972', 'd3b8bd9d-dabe-4f02-8f4a-61a40fa3b1fb', 'ec5dafe9-1e6f-47d5-8a29-268c7ba5ccf9');
-- smoney-hub (smoney-hub, spielstaette): 3 Events
UPDATE public.events SET ort_id = '534c1492-8b35-4783-9edc-58b1f5cea6ab' WHERE id IN ('35436648-3437-4f9a-a75b-0360f74fac8a', 'aa713329-6b61-40d1-9df2-673b00d7a0bf', '4947bdef-02e8-492c-82a7-9b8d84907e57');
-- Zurheide Feine Kost (zurheide-feine-kost, spielstaette): 3 Events
UPDATE public.events SET ort_id = '824da4d9-4b6c-4a02-b062-7e5284086606' WHERE id IN ('5591283d-ef93-409a-89ff-d45331b309a1', '5d05579d-2389-4403-85e6-a4163530b9ef', 'f35cb281-adb0-45b3-851a-ccf23532ef9a');
-- Fünfzehnwochen Golzheim - Projektraum / Offraum (fuenfzehnwochen-golzheim-projektraum-offraum, spielstaette): 3 Events
UPDATE public.events SET ort_id = '13d2627c-f62c-42a7-ad02-8c169e7ed6ad' WHERE id IN ('decb956b-32f2-489f-b06f-01abefe110de', 'd3e4a789-809d-4c43-bf5e-deaf89861b20', '9ee5004d-e0b5-4371-af6b-98c21eb129eb');
-- Wetthalle Neuss (wetthalle-neuss, spielstaette): 3 Events
UPDATE public.events SET ort_id = '59f20e50-4b53-495a-9089-497e34e081e1' WHERE id IN ('75ef80b6-e997-4e43-8555-d80806bfddae', 'c70284dc-bac8-4b67-9e06-a6e04ba2458e', '61bac55e-a201-4e6b-85a2-943edf390f99');
-- The Vinyl Room (the-vinyl-room, spielstaette): 3 Events
UPDATE public.events SET ort_id = 'df86020b-642b-492c-a598-80c029a4147d' WHERE id IN ('a924e592-bb5d-4733-b35f-baeaf5ca4bc8', '281f0d15-57fd-428f-b245-bdaee7b793a9', '828535fb-dff9-4bd5-93f7-2fce4962878d');
-- Em Pöötzke (em-poeoetzke, spielstaette): 3 Events
UPDATE public.events SET ort_id = '70b78f4c-0a3f-48d4-a2ec-5a70f048c5dd' WHERE id IN ('dcb735c8-4293-4a3f-afdb-69595c0eae7b', '9c3a9d66-2410-4f37-8c9f-34f81e8991cc', 'ddc3da5f-34ab-4564-8f87-2db549fe6205');
-- Das Dazwischen (das-dazwischen, spielstaette): 3 Events
UPDATE public.events SET ort_id = '408aabcb-a929-42f6-938f-365c42ce67b1' WHERE id IN ('2971c675-c1a2-4bb7-b816-9b3d8ab3de6c', '5bff53f7-8c10-42fe-81fa-49ba41afbe85', '15bf307e-17aa-4394-a465-0bef5bebc47d');
-- Pialana Manufaktur (pialana-manufaktur, spielstaette): 3 Events
UPDATE public.events SET ort_id = 'e004ec5c-6693-40ce-a79e-2887a745cb8b' WHERE id IN ('1fbb10e9-6f2e-4910-9700-542bfba9b94d', 'fac565d5-bf36-40e2-9bb7-2bfc369fd461', '76ad7fd6-80e3-441e-815c-271fac99c170');
-- IIK Düsseldorf Trainingszentrum, Raum F4 (iik-duesseldorf-trainingszentrum-raum-f4, spielstaette): 3 Events
UPDATE public.events SET ort_id = 'fe2b2f4b-c6ce-4718-8be6-1b6a6ead8ff4' WHERE id IN ('ca467e93-e2b6-4720-b10a-7b0494343d0d', '842c22d2-c5ec-471d-8f03-91589fd38e00', '1950a599-eae7-4dae-8e87-0530136c9ec4');
-- 4padel (4padel, spielstaette): 3 Events
UPDATE public.events SET ort_id = 'e8d37983-4d70-473e-980d-3d7c968c1324' WHERE id IN ('30da09cb-5e91-4213-bf66-a39e538fc7dd', '4f82a9f7-1feb-4556-9ce2-264cb01ac8cd', '4ced1046-1f85-46dc-9ce8-1d892cce25cd');
-- reinraum e.V. (reinraum-e-v, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'fb3e6566-f4b7-467e-817a-7b4f65556ba0' WHERE id IN ('a98adead-9ea4-4e4b-9664-5bd723f24c66', 'dc1879f7-05bb-41da-b7c8-f58bd717382d');
-- Roter Teppich (roter-teppich, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'e8732ad7-18a9-40ba-b356-5cf6bdc0d50e' WHERE id IN ('f01bb1ea-78ac-4a8e-bb36-f93fbb83bc17', 'c0880051-5fd0-4907-a138-9ce14b2271e0');
-- Kraeutelle - Naturkosmetik Workshops (kraeutelle-naturkosmetik-workshops, spielstaette): 2 Events
UPDATE public.events SET ort_id = '9fcd9806-fea2-48b8-94c9-bf9d4f9c2816' WHERE id IN ('01ed81ee-a075-417c-8ed0-bb02e7fa073a', 'e5dbe508-0a8d-4d5a-a45c-8c4d32c3f531');
-- MS RheinFantasie (ms-rheinfantasie, spielstaette): 2 Events
UPDATE public.events SET ort_id = '7f7d43f3-bcce-4ec9-ad7b-ced8f0579ee9' WHERE id IN ('001bcdaa-662a-4fad-936c-c51f185bd524', '4f268e9c-0eeb-4df8-8646-d5c07dde4d21');
-- SV Polizei (sv-polizei, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'ecd7c4ff-a273-42a2-b682-150473ec1cd7' WHERE id IN ('f76b8b09-76e9-41e3-b7a3-cc756053ddbe', '16f1e2fd-68cb-4908-b2cd-15fccc21651f');
-- Niemandsland e.V. (niemandsland-e-v, spielstaette): 2 Events
UPDATE public.events SET ort_id = '87f62fe5-6246-4596-9a42-ab463ef319aa' WHERE id IN ('ebac3ab0-7088-4a70-af8b-d0a41807a7f7', '22ea6a34-86ea-4bcc-a4a2-7fcf80bb0af8');
-- LaserTag Evolution Düsseldorf (lasertag-evolution-duesseldorf, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'b435901c-2805-4997-83bf-5f8c364320e0' WHERE id IN ('fd6dbe74-0215-4cb5-a26d-6a3ee334c13e', '2cbfc5a8-7228-498c-a9fe-9cc59a3a85a8');
-- Dein Ursprunghaus - Dein Ort für Bewusstwerdung (dein-ursprunghaus-dein-ort-fuer-bewusstwerdung, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'f19d652d-4b5a-4940-9f53-3f40355e8302' WHERE id IN ('9cb97269-a25d-4d1b-8507-8991679fefa8', '2281eb07-3961-4167-a0f7-1d72d2fbc82e');
-- VEN im INNSIDE Düsseldorf Derendorf (ven-im-innside-duesseldorf-derendorf, spielstaette): 2 Events
UPDATE public.events SET ort_id = '8a69f8c2-0059-4838-a387-f3927d35b6ac' WHERE id IN ('d5dc2bd5-0196-42b7-85ab-fb1626574408', '04980828-d80f-4d61-8164-49010fb94a4e');
-- Bergischer Löwe Düsseldorf (bergischer-loewe-duesseldorf, spielstaette): 2 Events
UPDATE public.events SET ort_id = '2903d425-b065-4ccc-87b1-15115316ac5a' WHERE id IN ('65c5c1ed-9d67-4182-8829-71a5b9315b59', 'eeb88372-8251-43b0-9a0e-853321a47a23');
-- Landtag NRW (landtag-nrw, spielstaette): 2 Events
UPDATE public.events SET ort_id = '79a410e1-141f-4bd9-9fcb-7f6f29d31d23' WHERE id IN ('6b69a490-cd50-4af5-8470-95204f0d5d1b', '05b28198-061a-4037-a7dc-15cced8725be');
-- Gare Du Neuss (gare-du-neuss, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'b8ed0702-ef7b-4388-addd-ea4b3470b11e' WHERE id IN ('fa0ace7f-6ff3-4921-b3a6-eb46c66058bd', '7d4d6ac5-5f9d-4ff4-bc64-844055714f45');
-- La bottega del gusto (la-bottega-del-gusto, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'fb3fdded-d46c-4d0e-adce-0802793eb945' WHERE id IN ('6870df27-f46f-406c-8686-8bd8b839ab59', 'caaefc58-bf6d-427b-a664-6be02920e2dc');
-- ZERO foundation (zero-foundation, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'fd9b4048-ff0f-4fb7-a221-b348ba653adc' WHERE id IN ('88a1939a-05f4-4518-9998-9d0d6d1e2fcf', '0a0c789e-6304-4b4b-958e-6b64352d00bd');
-- Kugel Eismanufaktur (kugel-eismanufaktur, spielstaette): 2 Events
UPDATE public.events SET ort_id = '6f7fe9b1-2149-49a5-80c0-cfe7b2a1b3d6' WHERE id IN ('ce9c2cc9-3bde-4bc5-9ebc-717313ccc010', '77bdce7d-8509-40eb-be7a-cb2250978749');
-- Hanaro Markt (hanaro-markt, spielstaette): 2 Events
UPDATE public.events SET ort_id = '17fc78e8-5e8b-48ed-bf6f-5682eb7219b4' WHERE id IN ('7340375f-f974-473a-b81f-873240be0510', '985293fc-ec0f-45bc-b8dc-527ed42deeb5');
-- KöX (koex, spielstaette): 2 Events
UPDATE public.events SET ort_id = '7906bec2-8ac7-4d6f-bb46-0b112c9f91e5' WHERE id IN ('e107e660-00e4-42dc-8d5b-8608365e35c9', 'f81e34b0-97cd-4322-a2b9-6cadc099b842');
-- BASH ROOMS Düsseldorf (bash-rooms-duesseldorf, spielstaette): 2 Events
UPDATE public.events SET ort_id = 'a6a0c493-d566-4276-81cb-9d852c394ced' WHERE id IN ('c06438da-7f98-4f5f-a739-b068c0d1da85', 'bc8ccc3f-689c-4d83-8017-d1b8e1d57110');

-- Kontrolle: Events mit ort_id je Typ des Orts
SELECT o.typ, count(*) FROM public.events e JOIN public.orte o ON o.id = e.ort_id GROUP BY o.typ ORDER BY 2 DESC;
